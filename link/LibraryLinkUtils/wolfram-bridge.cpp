#include "atomspace-bindings.h"
#include <iostream>
#include <sstream>
#include <unordered_map>
#include <algorithm>
#include <cmath>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <fcntl.h>

/**
 * Implementation of AtomSpace connector for WolfCog integration
 */

class AtomSpaceConnector::Impl {
public:
    int socket_fd;
    bool connected;
    std::string host;
    int port;
    std::unordered_map<std::string, std::shared_ptr<AtomSpaceNode>> node_cache;
    std::unordered_map<std::string, std::shared_ptr<AtomSpaceLink>> link_cache;
    
    Impl() : socket_fd(-1), connected(false), host("localhost"), port(17001) {}
    
    ~Impl() {
        if (connected && socket_fd >= 0) {
            close(socket_fd);
        }
    }
    
    bool connect_to_cogserver(const std::string& host_addr, int port_num) {
        // Create socket
        socket_fd = socket(AF_INET, SOCK_STREAM, 0);
        if (socket_fd < 0) {
            std::cerr << "Error creating socket" << std::endl;
            return false;
        }
        
        // Set socket to non-blocking
        int flags = fcntl(socket_fd, F_GETFL, 0);
        fcntl(socket_fd, F_SETFL, flags | O_NONBLOCK);
        
        // Setup server address
        struct sockaddr_in server_addr;
        server_addr.sin_family = AF_INET;
        server_addr.sin_port = htons(port_num);
        inet_pton(AF_INET, host_addr.c_str(), &server_addr.sin_addr);
        
        // Attempt connection
        int result = ::connect(socket_fd, (struct sockaddr*)&server_addr, sizeof(server_addr));
        
        if (result == 0 || (result < 0 && errno == EINPROGRESS)) {
            // Connection successful or in progress
            connected = true;
            host = host_addr;
            port = port_num;
            std::cout << "Connected to CogServer at " << host << ":" << port << std::endl;
            return true;
        } else {
            std::cerr << "Failed to connect to CogServer at " << host_addr << ":" << port_num << std::endl;
            close(socket_fd);
            socket_fd = -1;
            return false;
        }
    }
    
    bool send_command(const std::string& command) {
        if (!connected || socket_fd < 0) {
            return false;
        }
        
        std::string full_command = command + "\n";
        ssize_t sent = send(socket_fd, full_command.c_str(), full_command.length(), MSG_NOSIGNAL);
        
        if (sent < 0) {
            std::cerr << "Error sending command to CogServer" << std::endl;
            connected = false;
            return false;
        }
        
        return true;
    }
    
    std::string receive_response() {
        if (!connected || socket_fd < 0) {
            return "";
        }
        
        char buffer[4096];
        ssize_t received = recv(socket_fd, buffer, sizeof(buffer) - 1, MSG_DONTWAIT);
        
        if (received > 0) {
            buffer[received] = '\0';
            return std::string(buffer);
        } else if (received < 0 && errno != EWOULDBLOCK && errno != EAGAIN) {
            std::cerr << "Error receiving from CogServer" << std::endl;
            connected = false;
        }
        
        return "";
    }
};

// AtomSpaceConnector implementation
AtomSpaceConnector::AtomSpaceConnector() : pimpl(std::make_unique<Impl>()) {}

AtomSpaceConnector::~AtomSpaceConnector() = default;

bool AtomSpaceConnector::connect(const std::string& host, int port) {
    return pimpl->connect_to_cogserver(host, port);
}

void AtomSpaceConnector::disconnect() {
    if (pimpl->connected && pimpl->socket_fd >= 0) {
        close(pimpl->socket_fd);
        pimpl->socket_fd = -1;
        pimpl->connected = false;
        std::cout << "Disconnected from CogServer" << std::endl;
    }
}

bool AtomSpaceConnector::is_connected() const {
    return pimpl->connected;
}

std::shared_ptr<AtomSpaceNode> AtomSpaceConnector::create_concept_node(const std::string& name) {
    // Check cache first
    std::string cache_key = "ConceptNode_" + name;
    auto it = pimpl->node_cache.find(cache_key);
    if (it != pimpl->node_cache.end()) {
        return it->second;
    }
    
    // Create new node
    auto node = std::make_shared<AtomSpaceNode>("ConceptNode", name);
    
    // Send to CogServer if connected
    if (is_connected()) {
        std::string command = "(ConceptNode \"" + name + "\")";
        if (pimpl->send_command(command)) {
            std::cout << "Created ConceptNode: " << name << std::endl;
        }
    }
    
    // Cache the node
    pimpl->node_cache[cache_key] = node;
    return node;
}

std::shared_ptr<AtomSpaceNode> AtomSpaceConnector::create_predicate_node(const std::string& name) {
    std::string cache_key = "PredicateNode_" + name;
    auto it = pimpl->node_cache.find(cache_key);
    if (it != pimpl->node_cache.end()) {
        return it->second;
    }
    
    auto node = std::make_shared<AtomSpaceNode>("PredicateNode", name);
    
    if (is_connected()) {
        std::string command = "(PredicateNode \"" + name + "\")";
        pimpl->send_command(command);
    }
    
    pimpl->node_cache[cache_key] = node;
    return node;
}

std::shared_ptr<AtomSpaceNode> AtomSpaceConnector::create_number_node(double value) {
    std::string name = std::to_string(value);
    std::string cache_key = "NumberNode_" + name;
    auto it = pimpl->node_cache.find(cache_key);
    if (it != pimpl->node_cache.end()) {
        return it->second;
    }
    
    auto node = std::make_shared<AtomSpaceNode>("NumberNode", name);
    
    if (is_connected()) {
        std::string command = "(NumberNode " + name + ")";
        pimpl->send_command(command);
    }
    
    pimpl->node_cache[cache_key] = node;
    return node;
}

std::shared_ptr<AtomSpaceLink> AtomSpaceConnector::create_inheritance_link(
    std::shared_ptr<AtomSpaceNode> child,
    std::shared_ptr<AtomSpaceNode> parent) {
    
    auto link = std::make_shared<AtomSpaceLink>("InheritanceLink");
    link->add_outgoing_node(child);
    link->add_outgoing_node(parent);
    
    if (is_connected()) {
        std::string command = "(InheritanceLink " + child->to_scheme() + " " + parent->to_scheme() + ")";
        pimpl->send_command(command);
    }
    
    return link;
}

bool AtomSpaceConnector::send_scheme_command(const std::string& command) {
    if (!is_connected()) {
        std::cerr << "Not connected to CogServer" << std::endl;
        return false;
    }
    
    return pimpl->send_command(command);
}

std::string AtomSpaceConnector::evaluate_scheme(const std::string& expression) {
    if (!send_scheme_command(expression)) {
        return "";
    }
    
    // Wait a moment for response
    usleep(100000); // 100ms
    
    return pimpl->receive_response();
}

size_t AtomSpaceConnector::count_nodes() const {
    return pimpl->node_cache.size();
}

size_t AtomSpaceConnector::count_links() const {
    return pimpl->link_cache.size();
}

std::string AtomSpaceConnector::wolf_to_atomspace(const std::string& wolf_expression) {
    // Convert Wolf symbolic expressions to AtomSpace format
    std::string result = wolf_expression;
    
    // Replace Wolf symbolic operators with AtomSpace equivalents
    std::unordered_map<std::string, std::string> conversions = {
        {"∇", "GradientOperator"},
        {"∂", "PartialDerivative"},
        {"⊗", "TensorProduct"},
        {"Φ", "PhiFunction"},
        {"Ω", "OmegaSpace"},
        {"∑", "SummationOperator"}
    };
    
    for (const auto& conv : conversions) {
        size_t pos = 0;
        while ((pos = result.find(conv.first, pos)) != std::string::npos) {
            result.replace(pos, conv.first.length(), conv.second);
            pos += conv.second.length();
        }
    }
    
    // Wrap in ConceptNode if it's a simple expression
    if (result.find("(") == std::string::npos) {
        result = "(ConceptNode \"" + result + "\")";
    }
    
    return result;
}

std::string AtomSpaceConnector::atomspace_to_wolf(const std::string& atomspace_data) {
    std::string result = atomspace_data;
    
    // Convert AtomSpace format back to Wolf symbolic expressions
    std::unordered_map<std::string, std::string> conversions = {
        {"GradientOperator", "∇"},
        {"PartialDerivative", "∂"},
        {"TensorProduct", "⊗"},
        {"PhiFunction", "Φ"},
        {"OmegaSpace", "Ω"},
        {"SummationOperator", "∑"}
    };
    
    for (const auto& conv : conversions) {
        size_t pos = 0;
        while ((pos = result.find(conv.first, pos)) != std::string::npos) {
            result.replace(pos, conv.first.length(), conv.second);
            pos += conv.second.length();
        }
    }
    
    // Remove ConceptNode wrapping if present
    if (result.find("(ConceptNode \"") == 0 && result.back() == ')') {
        result = result.substr(13, result.length() - 15); // Remove (ConceptNode " and ")
    }
    
    return result;
}

// AtomSpaceNode implementation
AtomSpaceNode::AtomSpaceNode(const std::string& node_type, const std::string& node_name)
    : type(node_type), name(node_name), truth_value_strength(1.0), truth_value_confidence(1.0) {}

std::string AtomSpaceNode::to_scheme() const {
    return "(" + type + " \"" + name + "\")";
}

std::string AtomSpaceNode::to_wolf_format() const {
    // Convert common AtomSpace node types to Wolf format
    if (type == "ConceptNode") {
        return name;
    } else if (type == "NumberNode") {
        return name;
    } else if (type == "PredicateNode") {
        return name + "()";
    }
    return name;
}

// AtomSpaceLink implementation
AtomSpaceLink::AtomSpaceLink(const std::string& link_type)
    : type(link_type), truth_value_strength(1.0), truth_value_confidence(1.0) {}

void AtomSpaceLink::add_outgoing_node(std::shared_ptr<AtomSpaceNode> node) {
    outgoing_nodes.push_back(node);
}

std::string AtomSpaceLink::to_scheme() const {
    std::stringstream ss;
    ss << "(" << type;
    
    for (const auto& node : outgoing_nodes) {
        ss << " " << node->to_scheme();
    }
    
    ss << ")";
    return ss.str();
}

std::string AtomSpaceLink::to_wolf_format() const {
    if (type == "InheritanceLink" && outgoing_nodes.size() == 2) {
        return outgoing_nodes[0]->to_wolf_format() + " ⊆ " + outgoing_nodes[1]->to_wolf_format();
    } else if (type == "EvaluationLink" && outgoing_nodes.size() >= 2) {
        std::string result = outgoing_nodes[0]->to_wolf_format() + "(";
        for (size_t i = 1; i < outgoing_nodes.size(); ++i) {
            if (i > 1) result += ", ";
            result += outgoing_nodes[i]->to_wolf_format();
        }
        result += ")";
        return result;
    }
    
    // Default format
    std::string result = type + "(";
    for (size_t i = 0; i < outgoing_nodes.size(); ++i) {
        if (i > 0) result += ", ";
        result += outgoing_nodes[i]->to_wolf_format();
    }
    result += ")";
    return result;
}

// SymbolicMemoryInterface implementation
SymbolicMemoryInterface::SymbolicMemoryInterface(std::shared_ptr<AtomSpaceConnector> connector)
    : atomspace_connector(connector) {}

bool SymbolicMemoryInterface::store_symbolic_memory(const std::string& space, 
                                                   const std::string& symbolic_data) {
    if (!atomspace_connector->is_connected()) {
        return false;
    }
    
    // Create space node
    auto space_node = atomspace_connector->create_concept_node("Space_" + space);
    
    // Create data node
    auto data_node = atomspace_connector->create_concept_node(symbolic_data);
    
    // Create membership link
    auto membership_link = atomspace_connector->create_inheritance_link(data_node, space_node);
    
    std::cout << "Stored symbolic memory in space " << space << ": " << symbolic_data << std::endl;
    return true;
}

std::string SymbolicMemoryInterface::retrieve_symbolic_memory(const std::string& space, 
                                                             const std::string& query) {
    if (!atomspace_connector->is_connected()) {
        return "";
    }
    
    // Query the AtomSpace for data in the specified space
    std::string scheme_query = "(cog-execute! (GetLink (InheritanceLink (VariableNode \"$x\") (ConceptNode \"Space_" + space + "\"))))";
    
    return atomspace_connector->evaluate_scheme(scheme_query);
}

void SymbolicMemoryInterface::record_symbolic_evolution(const std::string& before, 
                                                       const std::string& after,
                                                       const std::string& operation) {
    if (!atomspace_connector->is_connected()) {
        return;
    }
    
    // Create evolution nodes
    auto before_node = atomspace_connector->create_concept_node("State_" + before);
    auto after_node = atomspace_connector->create_concept_node("State_" + after);
    auto operation_node = atomspace_connector->create_predicate_node("Operation_" + operation);
    
    // Create evolution link
    auto evolution_link = std::make_shared<AtomSpaceLink>("EvaluationLink");
    evolution_link->add_outgoing_node(operation_node);
    evolution_link->add_outgoing_node(before_node);
    evolution_link->add_outgoing_node(after_node);
    
    std::string command = evolution_link->to_scheme();
    atomspace_connector->send_scheme_command(command);
    
    std::cout << "Recorded symbolic evolution: " << before << " --[" << operation << "]--> " << after << std::endl;
}

// WolfKernelUtils implementation
namespace WolfKernelUtils {
    
    std::string parse_wolf_expression(const std::string& wolf_expr) {
        AtomSpaceConnector connector;
        return connector.wolf_to_atomspace(wolf_expr);
    }
    
    bool execute_symbolic_operation(AtomSpaceConnector& connector,
                                  const std::string& operation,
                                  const std::vector<std::string>& operands) {
        if (!connector.is_connected()) {
            return false;
        }
        
        // Create operation predicate
        auto op_node = connector.create_predicate_node(operation);
        
        // Create operand nodes
        std::vector<std::shared_ptr<AtomSpaceNode>> operand_nodes;
        for (const auto& operand : operands) {
            operand_nodes.push_back(connector.create_concept_node(operand));
        }
        
        // Create evaluation link
        auto eval_link = std::make_shared<AtomSpaceLink>("EvaluationLink");
        eval_link->add_outgoing_node(op_node);
        for (const auto& node : operand_nodes) {
            eval_link->add_outgoing_node(node);
        }
        
        std::string command = eval_link->to_scheme();
        return connector.send_scheme_command(command);
    }
    
    MemoryStats get_memory_statistics(AtomSpaceConnector& connector) {
        MemoryStats stats;
        stats.node_count = connector.count_nodes();
        stats.link_count = connector.count_links();
        stats.complexity_score = std::log(stats.node_count + 1) * std::log(stats.link_count + 1);
        stats.memory_usage_mb = (stats.node_count * 64 + stats.link_count * 128) / (1024.0 * 1024.0); // Rough estimate
        
        return stats;
    }
}