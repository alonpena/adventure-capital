# Standard valuation report blueprint

The standard valuation report will be driven by `docs/report-blueprint.md` and implemented as a template-based renderer that consumes pipeline artifacts, report-only YAML sections, and derived sensitivity/MapValue outputs. This keeps the optimization and valuation core independent from presentation while allowing the report format to evolve as a product artifact.
