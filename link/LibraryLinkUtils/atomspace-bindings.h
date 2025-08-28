#ifndef ATOMSPACE_BINDINGS_H
#define ATOMSPACE_BINDINGS_H

#include <string>
#include <vector>
#include <memory>

// Forward declarations for AtomSpace integration
struct AtomSpaceNode;
struct AtomSpaceLink;

/**
 * AtomSpace Memory Graph Bindings for WolfCog
 * Provides C++ interface to OpenCog AtomSpace for symbolic kernels
 */

class AtomSpaceConnector {
public:
    AtomSpaceConnector();
    ~AtomSpaceConnector();
    
    // Connection management
    bool connect(const std::string& host = "localhost", int port = 17001);
    void disconnect();
    bool is_connected() const;
    
    // Atom creation and manipulation
    std::shared_ptr<AtomSpaceNode> create_concept_node(const std::string& name);
    std::shared_ptr<AtomSpaceNode> create_predicate_node(const std::string& name);
    std::shared_ptr<AtomSpaceNode> create_number_node(double value);
    
    std::shared_ptr<AtomSpaceLink> create_inheritance_link(
        std::shared_ptr<AtomSpaceNode> child,
        std::shared_ptr<AtomSpaceNode> parent
    );
    
    std::shared_ptr<AtomSpaceLink> create_evaluation_link(
        std::shared_ptr<AtomSpaceNode> predicate,
        const std::vector<std::shared_ptr<AtomSpaceNode>>& arguments
    );
    
    // Memory graph queries
    std::vector<std::shared_ptr<AtomSpaceNode>> find_nodes_by_name(const std::string& name);
    std::vector<std::shared_ptr<AtomSpaceLink>> find_incoming_links(
        std::shared_ptr<AtomSpaceNode> node
    );
    std::vector<std::shared_ptr<AtomSpaceNode>> find_outgoing_nodes(
        std::shared_ptr<AtomSpaceLink> link
    );
    
    // Symbolic operations
    bool send_scheme_command(const std::string& command);
    std::string evaluate_scheme(const std::string& expression);
    
    // Memory topology analysis
    size_t count_nodes() const;
    size_t count_links() const;
    double calculate_memory_complexity() const;
    
    // Wolf-specific symbolic conversion
    std::string wolf_to_atomspace(const std::string& wolf_expression);
    std::string atomspace_to_wolf(const std::string& atomspace_data);
    
private:
    class Impl;
    std::unique_ptr<Impl> pimpl;
};

/**
 * AtomSpace Node representation
 */
struct AtomSpaceNode {
    std::string type;  // "ConceptNode", "PredicateNode", etc.
    std::string name;
    double truth_value_strength;
    double truth_value_confidence;
    
    AtomSpaceNode(const std::string& node_type, const std::string& node_name);
    
    std::string to_scheme() const;
    std::string to_wolf_format() const;
};

/**
 * AtomSpace Link representation
 */
struct AtomSpaceLink {
    std::string type;  // "InheritanceLink", "EvaluationLink", etc.
    std::vector<std::shared_ptr<AtomSpaceNode>> outgoing_nodes;
    double truth_value_strength;
    double truth_value_confidence;
    
    AtomSpaceLink(const std::string& link_type);
    
    void add_outgoing_node(std::shared_ptr<AtomSpaceNode> node);
    std::string to_scheme() const;
    std::string to_wolf_format() const;
};

/**
 * Symbolic Memory Interface
 * High-level interface for symbolic memory operations
 */
class SymbolicMemoryInterface {
public:
    SymbolicMemoryInterface(std::shared_ptr<AtomSpaceConnector> connector);
    
    // Symbolic space operations
    bool store_symbolic_memory(const std::string& space, 
                              const std::string& symbolic_data);
    std::string retrieve_symbolic_memory(const std::string& space, 
                                       const std::string& query);
    
    // Evolution tracking
    void record_symbolic_evolution(const std::string& before, 
                                 const std::string& after,
                                 const std::string& operation);
    
    // Pattern matching
    std::vector<std::string> find_symbolic_patterns(const std::string& pattern);
    
    // Memory compression
    bool compress_symbolic_memory(const std::string& space);
    
    // Geometric memory operations
    std::vector<std::string> get_memory_neighbors(const std::string& concept, 
                                                double distance_threshold = 0.5);
    double calculate_concept_distance(const std::string& concept1, 
                                    const std::string& concept2);
    
private:
    std::shared_ptr<AtomSpaceConnector> atomspace_connector;
};

// Utility functions for Wolf kernel integration
namespace WolfKernelUtils {
    
    // Convert Wolf symbolic expressions to AtomSpace format
    std::string parse_wolf_expression(const std::string& wolf_expr);
    
    // Execute symbolic operations in AtomSpace
    bool execute_symbolic_operation(AtomSpaceConnector& connector,
                                  const std::string& operation,
                                  const std::vector<std::string>& operands);
    
    // Memory evolution utilities
    void snapshot_memory_state(AtomSpaceConnector& connector, 
                             const std::string& snapshot_id);
    bool restore_memory_state(AtomSpaceConnector& connector,
                            const std::string& snapshot_id);
    
    // Performance utilities
    struct MemoryStats {
        size_t node_count;
        size_t link_count;
        double complexity_score;
        double memory_usage_mb;
    };
    
    MemoryStats get_memory_statistics(AtomSpaceConnector& connector);
}

#endif // ATOMSPACE_BINDINGS_H