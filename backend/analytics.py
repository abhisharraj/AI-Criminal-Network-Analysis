import networkx as nx


class GraphAnalytics:

    def __init__(self, graph):

        self.graph = graph

        # Create a simple undirected graph for
        # network-level analytics.
        #
        # The original graph keeps direction and
        # relationship types.
        self.analysis_graph = nx.Graph()

        for node, data in graph.nodes(data=True):

            self.analysis_graph.add_node(
                node,
                **data
            )

        # Add unique connections
        for source, target in graph.edges():

            self.analysis_graph.add_edge(
                source,
                target
            )

    # ==================================================
    # 1. DEGREE CENTRALITY
    # ==================================================

    def degree_centrality(self):

        return nx.degree_centrality(
            self.analysis_graph
        )

    # ==================================================
    # 2. BETWEENNESS CENTRALITY
    # ==================================================

    def betweenness_centrality(self):

        return nx.betweenness_centrality(
            self.analysis_graph
        )

    # ==================================================
    # 3. COMMUNITY DETECTION
    # ==================================================

    def detect_communities(self):

        communities = (
            nx.community
            .greedy_modularity_communities(
                self.analysis_graph
            )
        )

        return communities

    # ==================================================
    # 4. SHORTEST PATH
    # ==================================================

    def shortest_path(self, source, target):

        try:

            return nx.shortest_path(
                self.analysis_graph,
                source=source,
                target=target
            )

        except nx.NetworkXNoPath:

            return None

        except nx.NodeNotFound:

            return None

    # ==================================================
    # 5. DISPLAY ANALYTICS
    # ==================================================

    def display_analytics(self):

        print("\n")
        print("=" * 50)
        print("GRAPH ANALYTICS")
        print("=" * 50)

        # ----------------------------------------------
        # Degree Centrality
        # ----------------------------------------------

        print("\nDEGREE CENTRALITY")
        print("-" * 30)

        degree_scores = self.degree_centrality()

        sorted_degree = sorted(
            degree_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        for node, score in sorted_degree:

            print(
                f"{node}: {score:.3f}"
            )

        # ----------------------------------------------
        # Betweenness Centrality
        # ----------------------------------------------

        print("\nBETWEENNESS CENTRALITY")
        print("-" * 30)

        betweenness_scores = (
            self.betweenness_centrality()
        )

        sorted_betweenness = sorted(
            betweenness_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        for node, score in sorted_betweenness:

            print(
                f"{node}: {score:.3f}"
            )

        # ----------------------------------------------
        # Communities
        # ----------------------------------------------

        print("\nCOMMUNITIES")
        print("-" * 30)

        communities = self.detect_communities()

        for index, community in enumerate(
            communities,
            start=1
        ):

            print(
                f"Community {index}: "
                f"{list(community)}"
            )