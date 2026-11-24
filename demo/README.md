# Demo: Origraphi

Interactive implementation of Origraphi: BioFabric with edge and node folding, as used in the studies.
The code predates the name Origraphi and calls folding "compression" or "collapsing".

## Running

The page uses JavaScript modules, so it must be served by a web server rather than opened
as a file. From this folder:

```bash
python -m http.server 8000
```

Then open <http://localhost:8000>. The page loads d3 from a CDN, so an internet connection is needed.
Use the buttons at the top to switch between networks.

## Contents

| File                                                   | Contents                                                        |
|--------------------------------------------------------|-----------------------------------------------------------------|
| `index.html`, `style.css`                              | Page and network selection                                      |
| `src/js/main.js`                                       | Entry point: loads a network and sets up the view               |
| `src/js/graph.js`, `vertex.js`, `edge.js`              | Graph data model                                                |
| `src/js/biofabric.js`, `biofabricrenderer.js`          | BioFabric layout and rendering, including edge and node folding |
| `src/js/CompressionMsg.js`, `depthicon.js`, `state.js` | Folding states, depth icons and shared view state               |
| `data/grafo*.json`                                     | Four of the Rome graphs used in the study tasks                 |
| `data/*-network.json`, `miserables.edges.json`         | Example networks                                                |
