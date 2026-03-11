High-level Component Overview
=============================

.. mermaid::

    ---
    config:
        theme: 'base'
        themeVariables:
            primaryColor: "#f0e2d2"
            secondaryColor: "#c2c5e0"
            tertiaryColor: "#cee8ef"
            primaryTextColor: "#000000"
    ---
    flowchart TD
        %% Layers
        subgraph L1["Configuration"]
            config["config<br/>Schemas, connector settings, FDP settings"]
        end

        subgraph L2["Input Layer"]
            connectors["connectors<br/>Connect to data sources"]
            extractors["extractors<br/>Extract raw data → DataFrame"]
        end

        subgraph L3["Processing Layer"]
            models["models<br/>Metadata schemas (Pydantic)"]
            transformers["transformers<br/>DataFrame → Model → RDF"]
            rdf_utils["rdf<br/>RDF graph utilities"]
        end

        subgraph L4["Output Layer"]
            fdp["fdp<br/>FAIR Data Point client"]
        end

        subgraph L5["Orchestration & Logging"]
            pipeline["pipeline<br/>Controls full process"]
            logging["logging.py<br/>Logs steps & results"]
        end

        %% Data Flow
        config --> pipeline

        pipeline --> connectors --> extractors --> transformers --> rdf_utils --> fdp

        models --> transformers

        %% Logging
        pipeline --> logging
        connectors --> logging
        extractors --> logging
        transformers --> logging
        fdp --> logging
