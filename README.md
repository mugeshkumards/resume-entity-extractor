# Resume Entity Extractor

Streamlit app to extract entities from resumes (PDF/DOCX/TXT): name, email, phone, links, skills, education, and experience.

## Run locally (without Docker)

```bash
# In repo root
pip install -r requirements.txt
python -m spacy download en_core_web_sm
streamlit run app.py
```

App will be available at http://localhost:8501

## Docker

### Build
```bash
docker build -t resume-entity-extractor:latest .
```

### Run
```bash
docker run --rm -p 8501:8501 resume-entity-extractor:latest
```

Open http://localhost:8501

## Publish to GitHub

1. Create a new GitHub repository (empty).
2. Initialize and push:
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

## Optional: GitHub Actions to build Docker image
A workflow is included at `.github/workflows/docker.yml` to build the image on each push. To also publish to GitHub Container Registry (GHCR):

1. Ensure your repo is public or you have appropriate GHCR permissions.
2. Add the following repository secrets:
   - `GHCR_USERNAME` = your GitHub username
   - `GHCR_TOKEN` = a Classic Personal Access Token with `write:packages` and `read:packages`
3. Update the `IMAGE_NAME` variable in the workflow if desired.

Then push to `main` and the workflow will build and push the image.

## Notes
- First run may download NLTK resources at runtime.
- The Docker image downloads `en_core_web_sm` during build.
