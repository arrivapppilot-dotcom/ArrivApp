# ArrivApp Frontend

Frontend for the ArrivApp student check-in system.

## Production Setup

This project uses **Tailwind CSS** in production via the standalone CLI (no CDN).

### Prerequisites

- Python 3.x (for serving static files)
- The Tailwind CSS standalone binary (already included as `tailwindcss`)

### CSS Build Process

The project uses a custom input CSS file (`src/input.css`) that imports Tailwind and includes custom styles. The build process generates the production `styles.css` file.

#### Build CSS (Production)

```bash
npm run build:css
```

This command:
- Reads from `src/input.css`
- Processes all Tailwind directives
- Includes custom styles
- Outputs minified CSS to `styles.css`

#### Watch Mode (Development)

```bash
npm run watch:css
```

This watches for changes and rebuilds automatically.

### Running the Server

```bash
npm run serve
# or
python3 -m http.server 8080
```

Then visit: http://localhost:8080/login.html

### File Structure

```
frontend/
├── src/
│   └── input.css          # Source CSS with Tailwind imports
├── styles.css             # Generated production CSS (minified)
├── tailwindcss            # Standalone Tailwind CLI binary
├── *.html                 # Application pages
├── *.js                   # Client-side JavaScript
└── package.json           # Build scripts
```

### Important Notes

- **Do not edit `styles.css` directly** - it's auto-generated
- All custom styles should go in `src/input.css`
- Run `npm run build:css` before deploying to production
- The CDN version has been removed for production readiness

### Deployment

1. Ensure CSS is built: `npm run build:css`
2. Deploy all files except:
   - `node_modules/`
   - `tailwindcss` binary
   - `*.bak*` files
3. The `styles.css` file contains all required styles

### Available Scripts

- `npm run build:css` - Build production CSS (minified)
- `npm run watch:css` - Watch and rebuild CSS on changes
- `npm run serve` - Start development server on port 8080
