# CI/CD Pipeline Documentation

## 🔄 Overview

This project uses **GitHub Actions** for Continuous Integration and Continuous Deployment.

## 📋 Pipeline Jobs

### 1. **Lint** - Code Quality Check
- Runs `black` for code formatting check
- Runs `isort` for import sorting check  
- Runs `flake8` for linting

### 2. **Test** - Unit & Integration Tests
- Sets up PostgreSQL test database
- Runs pytest with coverage
- Uploads coverage to Codecov

### 3. **Build** - Docker Image Build
- Builds Docker image
- Tests the built image

### 4. **Deploy** - Deploy to Render
- Triggers only on `main` branch pushes
- Calls Render deploy hook
- Auto-deploys to production

## 🔐 Required GitHub Secrets

Add this secret in **GitHub Repository Settings → Secrets and variables → Actions**:

```
RENDER_DEPLOY_HOOK_URL
```

### How to get Render Deploy Hook URL:

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Select your service: `chat_real_time`
3. Go to **Settings** tab
4. Scroll down to **Deploy Hook** section
5. Click **Create Deploy Hook**
6. Copy the generated URL (looks like: `https://api.render.com/deploy/srv-xxx?key=yyy`)
7. Add to GitHub Secrets as `RENDER_DEPLOY_HOOK_URL`

## 🚀 Triggering Deployments

### Automatic Deployment
- Any push to `main` branch triggers auto-deploy to Render

### Manual Deployment
1. Go to **Actions** tab on GitHub
2. Select **CI/CD Pipeline** workflow
3. Click **Run workflow**
4. Select branch and click **Run workflow** button

## 📊 Test Coverage

Coverage reports are automatically uploaded to [Codecov](https://codecov.io/) (optional).

## ✅ Branch Protection Rules

Recommended settings for `main` branch protection:

- ✅ Require pull request before merging
- ✅ Require status checks to pass before merging
  - `lint` check must pass
  - `test` check must pass
  - `build` check must pass
- ✅ Require branches to be up to date before merging
- ✅ Require conversation resolution before merging

## 🧪 Running Tests Locally

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=app --cov-report=html

# View coverage in browser
open htmlcov/index.html  # Mac/Linux
start htmlcov/index.html  # Windows
```

## 🎨 Code Formatting (Locally)

```bash
# Format code with Black
black app/ --line-length 120

# Sort imports
isort app/

# Check linting
flake8 app/
```

## 📈 Pipeline Status Badge

Add this to your `README.md` to show CI/CD status:

```markdown
![CI/CD](https://github.com/eat3torice/chat_real_time/workflows/CI%2FCD%20Pipeline/badge.svg)
```

## 🐛 Troubleshooting

### Tests fail locally but pass on CI
- Check Python version matches (3.11)
- Ensure all dependencies installed
- Check environment variables

### Deploy fails
- Verify `RENDER_DEPLOY_HOOK_URL` secret is set correctly
- Check Render service is running
- Verify Render build logs for errors

### Docker build fails
- Check Dockerfile syntax
- Verify all files are copied correctly
- Check base image availability
