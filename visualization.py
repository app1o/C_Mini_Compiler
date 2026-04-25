import networkx as nx
import matplotlib.pyplot as plt
from parser import AST

def hierarchy_pos(G, root=None, width=1., vert_gap=0.2, vert_loc=0, xcenter=0.5):
    """
    Creates a hierarchical tree layout for NetworkX.
    """
    if not nx.is_tree(G):
        raise TypeError('cannot use hierarchy_pos on a graph that is not a tree')

    if root is None:
        if isinstance(G, nx.DiGraph):
            root = next(iter(nx.topological_sort(G))) 
        else:
            root = list(G.nodes)[0]

    def _hierarchy_pos(G, root, width=1., vert_gap=0.2, vert_loc=0, xcenter=0.5, pos=None, parent=None):
        if pos is None:
            pos = {root: (xcenter, vert_loc)}
        else:
            pos[root] = (xcenter, vert_loc)
            
        children = list(G.neighbors(root))
        if not isinstance(G, nx.DiGraph) and parent is not None:
            children.remove(parent)  
            
        if len(children) != 0:
            dx = width / len(children) 
            nextx = xcenter - width/2 - dx/2
            for child in children:
                nextx += dx
                pos = _hierarchy_pos(G,child, width=dx, vert_gap=vert_gap, 
                                    vert_loc=vert_loc-vert_gap, xcenter=nextx,
                                    pos=pos, parent=root)
        return pos
        
    return _hierarchy_pos(G, root, width, vert_gap, vert_loc, xcenter)

def build_graph(node, graph=None, parent_id=None, node_counter=None):
    if graph is None:
        graph = nx.DiGraph()
        node_counter = [0]
        
    if node is None:
        return graph, None
        
    current_id = f"node_{node_counter[0]}"
    node_counter[0] += 1
    
    if isinstance(node, AST):
        label = node.__class__.__name__
        
        # Add values/tokens directly to the node label for clarity
        if hasattr(node, 'value') and node.value is not None:
            label += f"\n({node.value})"
        elif hasattr(node, 'op') and getattr(node.op, 'type', None):
            label += f"\n({node.op.type.name})"
        elif hasattr(node, 'token') and getattr(node.token, 'type', None) and not hasattr(node, 'value'):
            label += f"\n({node.token.type.name})"
            
        graph.add_node(current_id, label=label)
        if parent_id is not None:
            graph.add_edge(parent_id, current_id)
            
        # Recurse through children
        for key, value in vars(node).items():
            if key in ["token", "op", "value"]:
                continue
            if isinstance(value, list):
                for item in value:
                    build_graph(item, graph, current_id, node_counter)
            elif isinstance(value, AST):
                build_graph(value, graph, current_id, node_counter)
                
    else:
        label = str(node)
        graph.add_node(current_id, label=label)
        if parent_id is not None:
            graph.add_edge(parent_id, current_id)
            
    return graph, current_id

def visualize_ast(ast_root):
    graph, root = build_graph(ast_root)
    if len(graph) == 0:
        print("Empty AST, nothing to visualize.")
        return
        
    plt.figure(figsize=(12, 8))
    plt.title("Abstract Syntax Tree Visualization", fontsize=16, fontweight='bold', color="#2E3440")
    
    # Try different layouts
    try:
        from networkx.drawing.nx_pydot import graphviz_layout
        pos = graphviz_layout(graph, prog="dot")
    except ImportError:
        try:
            pos = hierarchy_pos(graph, root)
        except Exception:
            pos = nx.spring_layout(graph, k=0.8, iterations=50)
            
    labels = nx.get_node_attributes(graph, 'label')
    
    nx.draw(
        graph, pos, labels=labels, with_labels=True, 
        node_size=2000, node_color="#D8DEE9", 
        edgecolors="#4C566A", linewidths=1.5,
        font_size=10, font_weight="bold", font_family="sans-serif",
        arrowsize=18, edge_color="#81A1C1", node_shape="o"
    )
    plt.margins(0.1)
    
    # Optional: ensure we show non-blocking if needed, but blocking is fine for a pop-up
    plt.show()

def visualize_errors(errors):
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.axis('off')
    
    if not errors:
        plt.title("Syntax Analysis Result", fontsize=16, color="#4C566A", weight='bold')
        ax.text(0.5, 0.5, "✅ Zero Syntax Errors!\nThe parser completed successfully.", 
                fontsize=16, color="#3FB950",
                ha='center', va='center', weight='bold')
    else:
        plt.title(f"Syntax Error Tracker: {len(errors)} Error(s)", fontsize=16, color="#F85149", weight='bold')
        y_pos = 0.95
        for i, err in enumerate(errors):
            msg = f"{i+1}. {err}"
            import textwrap
            wrapped = textwrap.fill(msg, 70)
            lines = wrapped.count('\n') + 1
            ax.text(0.02, y_pos, wrapped, fontsize=11, color="#F85149",
                    ha='left', va='top', family='monospace')
            y_pos -= (0.08 * lines)
            if y_pos < 0.1:
                ax.text(0.02, y_pos, f"... and {len(errors) - i - 1} more errors hidden.", fontsize=11, color="#8B949E")
                break
                
    plt.tight_layout()
    plt.show()
