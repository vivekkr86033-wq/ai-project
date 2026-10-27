# Introduction to Artificial Intelligence — Study Notes

## What is Artificial Intelligence?

Artificial Intelligence (AI) is the field of computer science that focuses on creating systems capable of performing tasks that normally require human intelligence. These tasks include learning, reasoning, problem-solving, perception, language understanding, and decision-making.

AI was founded as an academic discipline in 1956 at the Dartmouth Conference. Since then, it has gone through several waves of optimism, followed by periods of disappointment known as "AI winters."

## Intelligent Agents

An intelligent agent is a system that perceives its environment through sensors and acts upon that environment through actuators. A rational agent selects actions that maximize its expected performance measure, given its percept sequence and built-in knowledge.

Key properties of agents:
- **Autonomy**: The agent can operate without direct human intervention
- **Reactivity**: The agent responds to changes in its environment
- **Proactiveness**: The agent can take initiative to achieve its goals
- **Social ability**: The agent can interact with other agents or humans

## Search Algorithms

Search algorithms are fundamental to AI problem-solving. They explore a state space to find a path from an initial state to a goal state.

### Uninformed Search
- **Breadth-First Search (BFS)**: Explores all nodes at the current depth before moving to the next level. Complete and optimal for unit costs. Time and space complexity: O(b^d).
- **Depth-First Search (DFS)**: Explores as far as possible along each branch before backtracking. Not complete in infinite spaces. Space complexity: O(bm).

### Informed Search
- **A* Search**: Uses a heuristic function h(n) to estimate the cost from node n to the goal. Combines path cost g(n) with heuristic h(n). Optimal when heuristic is admissible and consistent.
- **Greedy Best-First Search**: Expands the node that appears closest to the goal. Not optimal but often fast.

## Machine Learning Basics

Machine Learning (ML) is a subset of AI that focuses on algorithms that improve through experience. Instead of being explicitly programmed, ML systems learn patterns from data.

### Types of Machine Learning:
1. **Supervised Learning**: Training with labeled data. Examples: classification, regression.
2. **Unsupervised Learning**: Finding patterns in unlabeled data. Examples: clustering, dimensionality reduction.
3. **Reinforcement Learning**: Learning through trial and error with rewards and penalties.

### Common Algorithms:
- Linear Regression
- Decision Trees
- Support Vector Machines (SVM)
- K-Nearest Neighbors (KNN)
- Random Forests

## Neural Networks

Neural networks are computing systems inspired by biological neural networks. They consist of layers of interconnected nodes (neurons) that process information.

### Architecture:
- **Input Layer**: Receives the raw data
- **Hidden Layers**: Perform computations and feature extraction
- **Output Layer**: Produces the final result

### Deep Learning:
Deep learning uses neural networks with many hidden layers (hence "deep"). It has achieved breakthrough results in:
- Image recognition (Convolutional Neural Networks)
- Natural language processing (Transformer architecture)
- Speech recognition
- Game playing (AlphaGo)

## Natural Language Processing

Natural Language Processing (NLP) enables computers to understand, interpret, and generate human language.

### Key NLP Tasks:
- Text classification
- Named entity recognition
- Sentiment analysis
- Machine translation
- Question answering
- Text summarization

### Retrieval-Augmented Generation (RAG):
RAG combines information retrieval with text generation. It first retrieves relevant documents from a knowledge base, then uses an LLM to generate answers grounded in the retrieved context. This reduces hallucination and provides verifiable source citations.

## Ethics in AI

AI ethics addresses the moral implications of AI systems:
- **Bias and Fairness**: AI systems can perpetuate or amplify existing biases in training data
- **Transparency**: Users should understand how AI systems make decisions
- **Privacy**: AI systems must handle personal data responsibly
- **Accountability**: Clear responsibility for AI system outcomes
- **Safety**: AI systems should not cause harm
