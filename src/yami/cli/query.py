"""Query commands (search/query/get)."""

from __future__ import annotations

import json
from typing import Optional

import typer

from yami.core.context import get_context
from yami.output.formatter import format_output, print_error

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
