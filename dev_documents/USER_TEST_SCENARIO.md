# User Test Scenario & Tutorial Plan

## Tutorial Strategy

Our User Acceptance Testing (UAT) and tutorials are designed to be an executable, interactive experience that allows users to verify requirements and ensure reproducibility effortlessly. The core of this strategy revolves around creating a single, comprehensive tutorial file utilizing the `marimo` notebook framework.

We will provide a unified tutorial experience through **Mock Mode** (CI/no-api-key execution) and **Real Mode**.

- **Mock Mode**: The tutorial runs using predefined mock responses, which makes it perfect for fast CI/CD pipeline validations, automated UI testing, and learning the system's interface without incurring API costs.
- **Real Mode**: Connects to the actual OpenRouter API (or configured backend LLMs) to perform live parsing, multi-dimensional knowledge extraction, and dynamic node reorganization based on the `ALL_SPEC.md` requirements.

## Tutorial Plan

A **SINGLE** Marimo Text/Python file named `tutorials/UAT_AND_TUTORIAL.py` will be created to house all scenarios. It should contain all scenarios (Quick Start + Advanced) in one file for easy verification.

The tutorial will cover the following scenarios step-by-step:
1. **Scenario 1: The First Ingestion (Document to Semantic Tree)**
   - Target: `testfiles/test_text.txt` (or a sample PDF).
   - Verify: Multimodal VLM analysis, Semantic Chunking, and RAPTOR-based tree generation.
2. **Scenario 2: The Adaptive Question (Unlocking Knowledge)**
   - Target: Interactive UI interaction simulation.
   - Verify: Generation of adaptive questions and validation of user input to unlock a node.
3. **Scenario 3: The Feynman Recitation (Speech-to-Text)**
   - Target: Voice interaction simulation (using text input as fallback).
   - Verify: CAHM-based fact-checking and constructive AI feedback.
4. **Scenario 4: The Pivot KJ (Multi-Dimensional Reconstruction)**
   - Target: Applying a business framework (e.g., SWOT) or system architecture (e.g., Actor x State Transition).
   - Verify: Dynamic relocation of nodes, Web-Grounding (bias detection), and automated Markdown/Mermaid code export.

## Tutorial Validation

To validate the tutorial, execute the Marimo file using the standard runner:

```bash
uv run marimo run tutorials/UAT_AND_TUTORIAL.py --mode mock
```

The success criteria demand that the Marimo file executes correctly with no errors, rendering the expected outputs and diagrams for each scenario, demonstrating the seamless "frictionless" active learning platform envisioned in `matome2-0`.
