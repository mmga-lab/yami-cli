"""Query commands (search/query/get)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

import typer

from yami.core.context import get_context
from yami.output.formatter import format_output, print_error, print_info

app = typer.Typer(no_args_is_help=True)


def _get_vectors_from_sql(sql: str) -> List[List[float]]:
    """Execute SQL with DuckDB and return vectors."""
    try:
        import duckdb
    except ImportError:
        raise ImportError("duckdb is required for --sql option. Install with: uv add duckdb")

    conn = duckdb.connect()
    result = conn.execute(sql).fetchall()
    conn.close()

    vectors = []
    for row in result:
        # First column should be the vector
        vec = row[0]
        if isinstance(vec, (list, tuple)):
            vectors.append(list(vec))
        elif isinstance(vec, str):
            vectors.append(json.loads(vec))
        else:
            raise ValueError(f"Unexpected vector type: {type(vec)}")
    return vectors


def _get_random_vector(dim: int) -> List[float]:
    """Generate a random vector for testing."""
    import random
    return [random.random() for _ in range(dim)]


def _get_collection_vector_dim(client, collection_name: str, anns_field: Optional[str] = None) -> int:
    """Get vector dimension from collection schema."""
    from pymilvus import DataType

    vector_types = {
        DataType.FLOAT_VECTOR,
        DataType.FLOAT16_VECTOR,
        DataType.BFLOAT16_VECTOR,
        DataType.SPARSE_FLOAT_VECTOR,
        101, 102, 103, 104,  # Raw enum values
    }

    schema = client.describe_collection(collection_name)
    for field in schema.get("fields", []):
        field_type = field.get("type")
        # Handle both enum and string types
        if field_type in vector_types or (isinstance(field_type, str) and "VECTOR" in field_type):
            if anns_field is None or field.get("name") == anns_field:
                params = field.get("params", {})
                return params.get("dim", 128)
    return 128


@app.command()
def search(
    collection: str = typer.Argument(..., help="Collection name"),
    vector: Optional[str] = typer.Option(
        None,
        "--vector",
        "-v",
        help="Vector as JSON array (e.g., '[0.1, 0.2, 0.3]')",
    ),
    sql: Optional[str] = typer.Option(
        None,
        "--sql",
        help="SQL query to get vectors via DuckDB (e.g., \"SELECT vec FROM 'data.parquet'\")",
    ),
    random: bool = typer.Option(
        False,
        "--random",
        help="Use random vector for testing",
    ),
    dim: Optional[int] = typer.Option(
        None,
        "--dim",
        help="Vector dimension (for --random, auto-detected if not specified)",
    ),
    limit: int = typer.Option(
        10,
        "--limit",
        "-l",
        help="Maximum number of results to return",
    ),
    filter_expr: Optional[str] = typer.Option(
        None,
        "--filter",
        "-f",
        help="Filter expression (e.g., 'age > 20')",
    ),
    output_fields: Optional[str] = typer.Option(
        None,
        "--output-fields",
        help="Comma-separated list of fields to return",
    ),
    anns_field: Optional[str] = typer.Option(
        None,
        "--anns-field",
        help="Name of the vector field to search on",
    ),
    metric_type: Optional[str] = typer.Option(
        None,
        "--metric",
        "-m",
        help="Metric type override: COSINE, L2, IP",
    ),
    nprobe: Optional[int] = typer.Option(
        None,
        "--nprobe",
        help="Number of units to query (for IVF indexes)",
    ),
    ef: Optional[int] = typer.Option(
        None,
        "--ef",
        help="Search ef parameter (for HNSW indexes)",
    ),
    partition: Optional[str] = typer.Option(
        None,
        "--partition",
        "-p",
        help="Partition names (comma-separated)",
    ),
) -> None:
    """Perform vector similarity search.

    \b
    Vector input methods (use one):
      --vector  JSON array directly
      --sql     Query via DuckDB (Parquet, CSV, JSON, etc.)
      --random  Random vector for testing

    \b
    Examples:
      # Direct vector input
      yami query search my_col -v '[0.1, 0.2, ...]'

      # From Parquet file
      yami query search my_col --sql "SELECT vec FROM 'data.parquet' WHERE id=1"

      # From CSV file
      yami query search my_col --sql "SELECT embedding FROM 'vectors.csv' LIMIT 1"

      # From JSON file (wrapped: {"vec": [...]})
      yami query search my_col --sql "SELECT vec FROM read_json('query.json')"

      # From JSON file (raw array: [...])
      yami query search my_col --sql "SELECT list(json) FROM read_json('query.json')"

      # Batch search from multiple vectors
      yami query search my_col --sql "SELECT embedding FROM 'data.parquet' LIMIT 5"

      # Random vector for testing
      yami query search my_col --random
    """
    ctx = get_context()
    client = ctx.get_client()

    try:
        query_vectors = None

        # Determine vector source
        sources = sum([
            vector is not None,
            sql is not None,
            random,
        ])

        if sources == 0:
            print_error("Must specify one of: --vector, --sql, or --random")
            raise typer.Exit(1)
        if sources > 1:
            print_error("Only one vector source allowed")
            raise typer.Exit(1)

        if vector:
            # Direct JSON vector
            query_vectors = [json.loads(vector)]
            print_info(f"Using vector with {len(query_vectors[0])} dimensions")

        elif sql:
            # DuckDB SQL query
            query_vectors = _get_vectors_from_sql(sql)
            if not query_vectors:
                print_error("SQL query returned no vectors")
                raise typer.Exit(1)
            print_info(f"Loaded {len(query_vectors)} vector(s) from SQL query")

        elif random:
            # Random vector for testing
            vec_dim = dim or _get_collection_vector_dim(client, collection, anns_field)
            query_vectors = [_get_random_vector(vec_dim)]
            print_info(f"Using random vector with {vec_dim} dimensions")

        # Parse output fields
        fields = None
        if output_fields:
            fields = [f.strip() for f in output_fields.split(",")]

        # Parse partitions
        partitions = None
        if partition:
            partitions = [p.strip() for p in partition.split(",")]

        # Build search params
        search_params = {}
        if metric_type:
            search_params["metric_type"] = metric_type
        if nprobe:
            search_params["nprobe"] = nprobe
        if ef:
            search_params["ef"] = ef

        results = client.search(
            collection_name=collection,
            data=query_vectors,
            filter=filter_expr or "",
            limit=limit,
            output_fields=fields or ["*"],
            search_params=search_params if search_params else None,
            anns_field=anns_field,
            partition_names=partitions,
        )

        # Flatten results for display
        if results and len(results) > 0:
            all_results = []
            for batch_idx, batch in enumerate(results):
                for hit in batch:
                    item = {"id": hit.get("id"), "distance": hit.get("distance")}
                    if len(results) > 1:
                        item["_query_idx"] = batch_idx
                    entity = hit.get("entity", {})
                    item.update(entity)
                    all_results.append(item)
            format_output(all_results, ctx.output, title="Search Results")
        else:
            format_output([], ctx.output, title="Search Results")

    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON: {e}")
        raise typer.Exit(1)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("query")
def query_cmd(
    collection: str = typer.Argument(..., help="Collection name"),
    filter_expr: Optional[str] = typer.Option(
        None,
        "--filter",
        "-f",
        help="Filter expression (e.g., 'age > 20')",
    ),
    ids: Optional[str] = typer.Option(
        None,
        "--ids",
        "-i",
        help="Comma-separated list of IDs to query",
    ),
    output_fields: Optional[str] = typer.Option(
        None,
        "--output-fields",
        "-o",
        help="Comma-separated list of fields to return",
    ),
    limit: Optional[int] = typer.Option(
        None,
        "--limit",
        "-l",
        help="Maximum number of results (for filter query)",
    ),
    partition: Optional[str] = typer.Option(
        None,
        "--partition",
        "-p",
        help="Partition names (comma-separated)",
    ),
) -> None:
    """Query data using filter expression or IDs."""
    if not filter_expr and not ids:
        print_error("Either --filter or --ids is required")
        raise typer.Exit(1)

    ctx = get_context()
    client = ctx.get_client()

    try:
        # Parse output fields
        fields = ["*"]
        if output_fields:
            fields = [f.strip() for f in output_fields.split(",")]

        # Parse partitions
        partitions = None
        if partition:
            partitions = [p.strip() for p in partition.split(",")]

        kwargs = {
            "collection_name": collection,
            "output_fields": fields,
        }

        if ids:
            # Parse IDs
            id_list = [x.strip() for x in ids.split(",")]
            try:
                kwargs["ids"] = [int(x) for x in id_list]
            except ValueError:
                kwargs["ids"] = id_list
        else:
            kwargs["filter"] = filter_expr

        if partitions:
            kwargs["partition_names"] = partitions

        results = client.query(**kwargs)

        # Apply limit if specified
        if limit and len(results) > limit:
            results = results[:limit]

        format_output(results, ctx.output, title="Query Results")

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def get(
    collection: str = typer.Argument(..., help="Collection name"),
    ids: str = typer.Argument(..., help="Comma-separated list of IDs"),
    output_fields: Optional[str] = typer.Option(
        None,
        "--output-fields",
        "-o",
        help="Comma-separated list of fields to return",
    ),
    partition: Optional[str] = typer.Option(
        None,
        "--partition",
        "-p",
        help="Partition names (comma-separated)",
    ),
) -> None:
    """Get entities by IDs (shorthand for query by IDs)."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        # Parse IDs
        id_list = [x.strip() for x in ids.split(",")]
        try:
            parsed_ids = [int(x) for x in id_list]
        except ValueError:
            parsed_ids = id_list

        # Parse output fields
        fields = ["*"]
        if output_fields:
            fields = [f.strip() for f in output_fields.split(",")]

        # Parse partitions
        partitions = None
        if partition:
            partitions = [p.strip() for p in partition.split(",")]

        results = client.get(
            collection_name=collection,
            ids=parsed_ids,
            output_fields=fields,
            partition_names=partitions,
        )

        format_output(results, ctx.output, title="Get Results")

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("hybrid-search")
def hybrid_search(
    collection: str = typer.Argument(..., help="Collection name"),
    req: List[str] = typer.Option(
        [],
        "--req",
        "-r",
        help="Search request as JSON: {\"field\": \"vec\", \"vector\": [...], \"limit\": 10}",
    ),
    file: Optional[str] = typer.Option(
        None,
        "--file",
        "-f",
        help="JSON file containing search requests",
    ),
    limit: int = typer.Option(
        10,
        "--limit",
        "-l",
        help="Final limit after ranking",
    ),
    output_fields: Optional[str] = typer.Option(
        None,
        "--output-fields",
        "-o",
        help="Comma-separated list of fields to return",
    ),
    ranker: str = typer.Option(
        "rrf",
        "--ranker",
        help="Ranking strategy: rrf or weighted",
    ),
    rrf_k: int = typer.Option(
        60,
        "--rrf-k",
        help="RRF parameter k (only for rrf ranker)",
    ),
    weights: Optional[str] = typer.Option(
        None,
        "--weights",
        "-w",
        help="Comma-separated weights for weighted ranker (e.g., '0.7,0.3')",
    ),
    partition: Optional[str] = typer.Option(
        None,
        "--partition",
        "-p",
        help="Partition names (comma-separated)",
    ),
) -> None:
    """Perform hybrid search across multiple vector fields.

    \b
    Hybrid search combines multiple vector searches and ranks results.

    \b
    Request format (JSON):
    {
        "field": "vector_field_name",
        "vector": [0.1, 0.2, ...],
        "limit": 10,
        "filter": "optional_filter",
        "params": {"nprobe": 10}
    }

    \b
    Examples:
        # Two vector fields with RRF ranking
        yami query hybrid-search my_col \\
            --req '{"field": "dense", "vector": [0.1, 0.2], "limit": 20}' \\
            --req '{"field": "sparse", "vector": {...}, "limit": 20}'

        # With weighted ranking
        yami query hybrid-search my_col --file requests.json \\
            --ranker weighted --weights 0.7,0.3

        # requests.json format:
        [
            {"field": "vec1", "vector": [...], "limit": 20},
            {"field": "vec2", "vector": [...], "limit": 20}
        ]
    """
    from pymilvus import AnnSearchRequest, RRFRanker, WeightedRanker

    ctx = get_context()
    client = ctx.get_client()

    try:
        # Parse search requests
        requests_data = []

        if file:
            # Load from file
            file_path = Path(file)
            if not file_path.exists():
                print_error(f"File not found: {file}")
                raise typer.Exit(1)
            requests_data = json.loads(file_path.read_text())
            if not isinstance(requests_data, list):
                requests_data = [requests_data]
        elif req:
            # Parse from --req options
            for r in req:
                requests_data.append(json.loads(r))
        else:
            print_error("Either --req or --file is required")
            raise typer.Exit(1)

        if len(requests_data) < 1:
            print_error("At least one search request is required")
            raise typer.Exit(1)

        # Build AnnSearchRequest objects
        ann_requests = []
        for r in requests_data:
            field = r.get("field")
            vector = r.get("vector")
            req_limit = r.get("limit", 10)
            filter_expr = r.get("filter", "")
            params = r.get("params", {})

            if not field:
                print_error("Each request must have a 'field' key")
                raise typer.Exit(1)
            if vector is None:
                print_error(f"Request for field '{field}' must have a 'vector' key")
                raise typer.Exit(1)

            ann_req = AnnSearchRequest(
                data=[vector],
                anns_field=field,
                param=params,
                limit=req_limit,
                expr=filter_expr if filter_expr else None,
            )
            ann_requests.append(ann_req)

        # Build ranker
        if ranker.lower() == "weighted":
            if weights:
                weight_list = [float(w.strip()) for w in weights.split(",")]
            else:
                # Equal weights
                weight_list = [1.0 / len(ann_requests)] * len(ann_requests)

            if len(weight_list) != len(ann_requests):
                print_error(
                    f"Number of weights ({len(weight_list)}) must match "
                    f"number of requests ({len(ann_requests)})"
                )
                raise typer.Exit(1)

            reranker = WeightedRanker(*weight_list)
            print_info(f"Using WeightedRanker with weights: {weight_list}")
        else:
            reranker = RRFRanker(k=rrf_k)
            print_info(f"Using RRFRanker with k={rrf_k}")

        # Parse output fields
        fields = None
        if output_fields:
            fields = [f.strip() for f in output_fields.split(",")]

        # Parse partitions
        partitions = None
        if partition:
            partitions = [p.strip() for p in partition.split(",")]

        # Execute hybrid search
        results = client.hybrid_search(
            collection_name=collection,
            reqs=ann_requests,
            ranker=reranker,
            limit=limit,
            output_fields=fields or ["*"],
            partition_names=partitions,
        )

        # Flatten results for display
        if results and len(results) > 0:
            flat_results = []
            for hit in results[0]:
                item = {"id": hit.get("id"), "distance": hit.get("distance")}
                entity = hit.get("entity", {})
                item.update(entity)
                flat_results.append(item)
            format_output(flat_results, ctx.output, title="Hybrid Search Results")
        else:
            format_output([], ctx.output, title="Hybrid Search Results")

    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON: {e}")
        raise typer.Exit(1)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
