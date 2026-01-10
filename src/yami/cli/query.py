"""Query commands (search/query/get)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

import typer

from yami.core.context import get_context
from yami.output.formatter import format_output, print_error, print_info

app = typer.Typer(no_args_is_help=True)


@app.command()
def search(
    collection: str = typer.Argument(..., help="Collection name"),
    vector: str = typer.Option(
        ...,
        "--vector",
        "-v",
        help="Vector to search (JSON array, e.g., '[0.1, 0.2, 0.3]')",
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
        "-o",
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
    """Perform vector similarity search."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        # Parse vector
        query_vector = json.loads(vector)
        if not isinstance(query_vector, list):
            print_error("Vector must be a JSON array")
            raise typer.Exit(1)

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
            data=[query_vector],
            filter=filter_expr or "",
            limit=limit,
            output_fields=fields or ["*"],
            search_params=search_params if search_params else None,
            anns_field=anns_field,
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
            format_output(flat_results, ctx.output, title="Search Results")
        else:
            format_output([], ctx.output, title="Search Results")

    except json.JSONDecodeError as e:
        print_error(f"Invalid vector JSON: {e}")
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
