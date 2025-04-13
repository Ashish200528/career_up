# Uploading Career Up to GitHub

This guide will help you create a zip file of this project and upload it to GitHub.

## Creating a Zip File

### Windows
1. Select all the files and folders in the project directory
2. Right-click and select "Send to" → "Compressed (zipped) folder"
3. Name the zip file `career-up.zip`

### macOS
1. Select all the files and folders in the project directory
2. Right-click and select "Compress Items"
3. This will create `Archive.zip` - rename it to `career-up.zip`

### Command Line (any OS with zip installed)
```bash
zip -r career-up.zip . -x "*.git*" -x "*.pyc" -x "__pycache__/*" -x "venv/*" -x "*.zip"
```

## Uploading to GitHub

### Create a New Repository
1. Go to [GitHub](https://github.com) and sign in
2. Click the "+" in the top right corner and select "New repository"
3. Name your repository (e.g., "career-up")
4. Add a description (optional)
5. Choose if you want the repository to be public or private
6. Click "Create repository"

### Option 1: Upload the Zip File
1. In your new repository, click the "Add file" button and select "Upload files"
2. Drag and drop your `career-up.zip` file or click to select it
3. Add a commit message like "Initial commit"
4. Click "Commit changes"

### Option 2: Upload via Git (Recommended)
1. Install Git if you haven't already
2. Open a terminal/command prompt
3. Navigate to your project directory
4. Initialize a Git repository:
   ```bash
   git init
   ```
5. Add all files:
   ```bash
   git add .
   ```
6. Commit your changes:
   ```bash
   git commit -m "Initial commit"
   ```
7. Link to your GitHub repository:
   ```bash
   git remote add origin https://github.com/your-username/career-up.git
   ```
8. Push your code:
   ```bash
   git push -u origin main
   ```
   (If your default branch is "master" instead of "main", use `git push -u origin master`)

## After Uploading
1. Make sure to add your API keys as repository secrets if you're planning to deploy your application
2. Verify that all files are uploaded correctly
3. Update the repository URL in your README.md if needed

## Troubleshooting
- If you see a message about unrelated histories when pushing, you can use:
  ```bash
  git push -u origin main --force
  ```
  (Use with caution as this will overwrite any existing content)
- If you're having issues with large files, consider using Git LFS (Large File Storage) 