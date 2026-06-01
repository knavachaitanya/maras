module.exports = {
  rootDir: "./",
  include: [
    "./frontend/src/**/*.{ts,tsx}",
    "./backend/**/*.py",
  ],
  exclude: [
    "node_modules",
    "__pycache__",
    ".next",
    "*.test.*",
  ],
  output: {
    type: "json",
    path: "./frontend/public/graph-data.json",
  },
  graph: {
    groupBy: "directory",
    showImports: true,
    showExports: true,
    highlight: ["agents/", "swarm/", "services/"],
  },
};
