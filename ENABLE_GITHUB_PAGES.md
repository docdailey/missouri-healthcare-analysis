# How to Enable GitHub Pages for Interactive Maps

GitHub Pages needs to be enabled in your repository settings. Here's how:

## Quick Setup (2 minutes)

1. **Go to Repository Settings**
   - Visit: https://github.com/docdailey/missouri-healthcare-analysis/settings
   - Scroll down to "Pages" section (in left sidebar under "Code and automation")

2. **Enable GitHub Pages**
   - Under "Source", select: **GitHub Actions**
   - Click Save

3. **Re-run the Workflow**
   - Go to: https://github.com/docdailey/missouri-healthcare-analysis/actions
   - Click on the failed workflow run
   - Click "Re-run all jobs"

4. **View Your Maps** (after ~2 minutes)
   - Landing Page: https://docdailey.github.io/missouri-healthcare-analysis/
   - Coverage Map: https://docdailey.github.io/missouri-healthcare-analysis/missouri_healthcare_coverage_map.html
   - RHC Map: https://docdailey.github.io/missouri-healthcare-analysis/missouri_rhcs_final_complete_100pct.html

## Alternative: Use Branch Deployment

If GitHub Actions doesn't work, you can use the simpler branch deployment:

1. Go to Settings → Pages
2. Under "Source", select: **Deploy from a branch**
3. Choose: **main** branch
4. Choose: **/docs** folder
5. Click Save

The maps will be available at the same URLs within 5-10 minutes.

## Verify It's Working

Once enabled, you'll see:
- ✅ Green checkmark on the Actions tab
- ✅ "Your site is live at..." message in Pages settings
- ✅ Maps viewable in any web browser

## Troubleshooting

If maps don't appear after 10 minutes:
1. Check that the `/docs` folder contains the HTML files
2. Try hard refresh in browser (Ctrl+Shift+R or Cmd+Shift+R)
3. Check repository is public (private repos need GitHub Pro for Pages)