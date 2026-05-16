#Esprit school of engineering : AI project (1st year ai engineering)
# Social Media Strategy & Brand Intelligence objective

An end-to-end AI project for marketing and startup consulting. It combines three main modules:

- visual post quality evaluation
- text/caption quality evaluation
- brand document generation

The repository contains notebooks, inference helpers, and a small web app used to run the pipeline.

## Project Goals

The project is designed to help startups and small businesses:

- evaluate the quality of social media visuals
- score captions and hashtags across platforms
- estimate engagement potential
- generate brand strategy documents from a simple startup brief
- export results in reusable formats such as JSON, Markdown, and PDF

## Main Modules

### 1. Visual Module

Files:

- [visual module.ipynb](visual%20module.ipynb)
- [visual_module_dataset_testing.ipynb](visual_module_dataset_testing.ipynb)
- [visual_inference.py](visual_inference.py)

What it does:

- trains a visual aesthetic scoring model on image datasets
- predicts visual quality for a post image
- explains predictions with Grad-CAM and attribute analysis
- saves trained weights and evaluation plots in the `results/` and `outputs/` folders

### 2. Text Module

Files:

- [text-module-notebook (1).ipynb](text-module-notebook%20%281%29.ipynb)
- [text module.ipynb](text%20module.ipynb)
- [text_inference.py](text_inference.py)
- [text_xai_inference.py](text_xai_inference.py)

What it does:

- extracts hand-crafted NLP features from captions
- trains a text-only model and a fusion model with metadata
- loads a transformer sentiment classifier
- scores text quality for Instagram, LinkedIn, Twitter, and Facebook
- supports both dataset-driven profiles and user-defined audience profiles
- exports model artifacts and benchmark JSON files to `outputs/`

### 3. Brand Document Generator

Files:

- [branding_document_generator.ipynb](branding_document_generator.ipynb)

What it does:

- builds a startup brief into a complete brand guideline document
- infers missing brand details from a short natural-language prompt
- generates brand strategy sections, visual identity guidance, and logo concepts
- exports the final document as Markdown, JSON, and PDF

## Supporting Files

- [app.py](app.py) and [run_server.py](run_server.py) for web/app execution
- [templates/](templates/) for front-end HTML templates
- [static/](static/) for static assets
- [outputs/](outputs/) for generated models, reports, and exported documents
- [results/](results/) for evaluation plots and experiment artifacts

## Installation

Create and activate a virtual environment, then install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

If you use the notebooks, make sure the Jupyter kernel points to the same environment.

## How to Run

### Web app

```bash
python run_server.py
```

### Notebooks

Open the notebook you want to run and execute the cells in order.

Recommended notebook flow:

1. Visual module notebook for image scoring
2. Text module notebook for caption scoring
3. Branding notebook for brand document generation

## Outputs

The project writes generated files to:

- `outputs/` for model configs, JSON exports, and generated assets
- `results/` for charts and evaluation artifacts

Common exported files include:

- trained model weights
- feature configuration JSON files
- platform benchmark JSON files
- PDF and Markdown brand documents
- generated logo previews and evaluation figures

## Data Sources

The project uses several Kaggle datasets for training and benchmarking, including:

- Instagram analytics data
- social media sentiment data
- social media engagement data
- aesthetic image quality data
- logo datasets for experimentation and branding assets

## Notes

- Some notebooks are exploratory and include tests, diagnostics, and comparison cells.
- The brand generator is rule-based and notebook-driven, with optional logo generation experiments.
- The repository is intended for experimentation, evaluation, and portfolio presentation.

## Suggested Commit Message

If you want a clean GitHub commit, a good message would be:

`Add project README with module overview and setup instructions`
