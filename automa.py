import networkx as nx

from cfg import *


class Automa:
    def __init__(self):
        self.dfa = nx.DiGraph()
        self.nfa = nx.DiGraph()

    def g2nfa(self, G: Graph):
        self.nfa.graph['alphabet'] = G.dig.graph['alphabet']
        for u, v, data in G.dig.edges(data=True):
            label = data.get('label', '')  # 获取边的标签
            if label:
                if label[0] == '#':
                    label = label[1:]
                else:
                    label = ''
            self.nfa.add_edge(u, v, label=label)

    def epsilon_closure(self, states):
        closure = set(states)
        queue = list(states)
        while queue:
            current_state = queue.pop()
            # 返回从current_state出发的所有空边的目的地
            epsilon_transitions = [key for key, value in self.nfa[current_state].items() if not value['label']]
            for state in epsilon_transitions:
                if state not in closure:
                    closure.add(state)
                    queue.append(state)
        return frozenset(closure)

    def nfa2dfa(self):
        initial_state = self.epsilon_closure({G.fucTable['main'][0].id})
        self.dfa.add_node(initial_state)
        unmarked_states = [initial_state]
        alphabet = set(self.nfa.graph['alphabet'])

        while unmarked_states:
            current_states = unmarked_states.pop(0)
            for symbol in alphabet:
                next_states = set()
                for state in current_states:
                    transitions = [key for key, value in self.nfa[state].items() if value['label']==symbol]
                    for transition_state in transitions:
                        next_states |= self.epsilon_closure({transition_state})
                if next_states:
                    next_state = frozenset(next_states)
                    if next_state not in self.dfa:
                        self.dfa.add_node(next_state)
                        unmarked_states.append(next_state)
                    self.dfa.add_edge(current_states, next_state, label=symbol)


    def drawnfa(self):
        pos = nx.spring_layout(self.nfa)
        edge_labels = nx.get_edge_attributes(self.nfa, 'label')
        nx.draw_networkx(self.nfa, pos, with_labels=True, arrows=True, node_size=300, font_size=8, arrowsize=20)
        nx.draw_networkx_edge_labels(self.nfa, pos, edge_labels=edge_labels, font_color='red')
        plt.show()
    def drawdfa(self):
        pos = nx.spring_layout(self.dfa)
        edge_labels = nx.get_edge_attributes(self.dfa, 'label')
        nx.draw_networkx(self.dfa, pos, with_labels=True, arrows=True, node_size=300, font_size=8, arrowsize=20)
        nx.draw_networkx_edge_labels(self.dfa, pos, edge_labels=edge_labels, font_color='red')
        plt.show()
    #TODO:TEST nfa->dfa,write better testcase
