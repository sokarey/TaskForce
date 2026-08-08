# GitHub Upload Guide for TaskForce (Manual Upload)

## Step 1: Create GitHub Repository

1. Go to [GitHub.com](https://github.com) and sign in
2. Click the "+" icon in the top-right corner
3. Select "New repository"
4. Fill in repository details:
   - **Repository name**: `TaskForce` (or your preferred name)
   - **Description**: `IT Administration Toolkit for Windows environments`
   - **Visibility**: Choose Public or Private
   - **Initialize with**: Leave all checkboxes unchecked
5. Click "Create repository"

## Step 2: Upload Files via GitHub Web Interface

After creating the repository, you'll see an option to "upload an existing file":

1. Click "uploading an existing file" link
2. Drag and drop your files from `C:\TaskForce-GitHub` folder
3. Or click "choose your files" to select files manually

## Files to Upload

Upload these files and folders from `C:\TaskForce-GitHub`:

**Main Files:**
- `TaskForce.py`
- `TaskForce.ps1`
- `domain_manager.py`
- `path_manager.py`
- `TF.ico`
- `README.md`
- `How To use.txt`
- `compile_instructions.txt`
- `GITHUB_UPLOAD_GUIDE.md`

**Configuration Files:**
- `domains.json`
- `app_paths.json`

**Directories:**
- `New Batch/` (upload as folder)
- `Excel/` (upload as folder)

**Git Configuration:**
- `.gitignore`

## Step 3: Commit and Upload

1. After adding files, you'll see a commit message box
2. Enter: "Initial commit - TaskForce IT Administration Toolkit"
3. Click "Commit changes" (green button)
4. Wait for upload to complete

## Step 4: Verify Upload

Go to your GitHub repository page and verify:
- All files are uploaded in correct structure
- README.md displays correctly on repository page
- No sensitive information is visible
- Folders are properly structured

## Tips for Manual Upload

**Uploading Folders:**
- GitHub web interface allows folder uploads
- Drag entire folders (New Batch, Excel) to maintain structure
- Make sure folder contents are included

**File Size Limits:**
- Individual files must be under 25MB
- Total repository size under 1GB for free accounts
- Large files should be excluded via .gitignore

**Upload Order:**
1. Upload main files first
2. Upload configuration files
3. Upload folders last to maintain structure

## Troubleshooting

**Upload Fails:**
- Check file sizes (under 25MB each)
- Ensure stable internet connection
- Try uploading files in smaller batches

**Folder Structure Issues:**
- Upload folders by dragging them, not individual files
- Verify folder contents are included
- Check that subdirectories are preserved

**Missing Files:**
- Refresh the upload page if files don't appear
- Check that you're in the correct repository
- Verify file paths are correct

## Post-Upload Checklist

- [ ] Repository is public/private as intended
- [ ] README.md displays correctly on repository page
- [ ] Configuration files contain placeholder values only
- [ ] No sensitive data in repository
- [ ] Folder structure is preserved
- [ ] All necessary files are present
- [ ] .gitignore file is included

## Next Steps

After successful upload:
1. Add repository topics/tags for discoverability
2. Set up GitHub Issues for bug tracking
3. Add a LICENSE file if you want to specify usage terms
4. Create releases for version management
5. Add repository description and website if applicable
