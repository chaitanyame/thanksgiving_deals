# Contributing to Slickdeals Black Friday Deals Tracker

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to this open-source project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## How to Contribute

### Reporting Bugs

1. Check if the issue already exists in [GitHub Issues](https://github.com/chaitanyame/thanksgiving_deals/issues)
2. If not, create a new issue with:
   - Clear, descriptive title
   - Steps to reproduce the problem
   - Expected vs actual behavior
   - Screenshots if applicable
   - Browser/OS information

### Suggesting Features

1. Open an issue with the `enhancement` label
2. Describe the feature and its use case
3. Explain how it benefits users

### Submitting Pull Requests

#### Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/thanksgiving_deals.git
   cd thanksgiving_deals
   ```
3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/chaitanyame/thanksgiving_deals.git
   ```

#### Development Workflow

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes

3. Test locally:
   ```bash
   # Test scraper
   python scripts/sync_combined.py
   
   # Test website
   python -m http.server 8000
   ```

4. Commit with clear messages:
   ```bash
   git commit -m "Add: brief description of change"
   ```

5. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

6. Open a Pull Request against `main`

### Commit Message Guidelines

Use conventional commit prefixes:
- `Add:` New feature or file
- `Fix:` Bug fix
- `Update:` Modify existing functionality
- `Remove:` Delete code or files
- `Refactor:` Code restructuring without behavior change
- `Docs:` Documentation changes
- `Style:` Formatting, CSS changes

Examples:
```
Add: New electronics subcategory for smart home devices
Fix: Price extraction regex for comma-separated values
Update: Mobile card layout for better readability
Docs: Add Docker setup instructions
```

## Code Style

### Python (`scripts/`)
- Follow PEP 8 guidelines
- Use descriptive variable names
- Add docstrings for functions
- Keep functions focused and small

### JavaScript (`js/app.js`)
- Use ES6+ syntax
- No external dependencies (vanilla JS only)
- Use `const` and `let`, avoid `var`
- Add comments for complex logic

### CSS (`css/styles.css`)
- Use CSS custom properties for theming
- Follow mobile-first responsive design
- Group related styles with comments
- Maintain dark/light theme parity

### HTML (`index.html`)
- Use semantic HTML5 elements
- Include accessibility attributes
- Keep structure clean and readable

## Areas for Contribution

### High-Priority
- 🏷️ Improve deal categorization accuracy
- 🏪 Add more store detection patterns
- 📱 Enhance mobile experience
- ♿ Accessibility improvements

### Good First Issues
- Fix typos in documentation
- Add new category keywords
- Improve error messages
- Add loading states

### Advanced
- Performance optimizations
- New filtering options
- Analytics integration
- PWA features

## Testing

Before submitting a PR:

1. **Scraper Testing**
   ```bash
   python scripts/sync_combined.py
   # Verify data/deals.json is valid and contains expected deals
   ```

2. **Frontend Testing**
   - Test in multiple browsers (Chrome, Firefox, Safari)
   - Test responsive design at different breakpoints
   - Verify dark/light theme works correctly
   - Check all filters and sorting options

3. **Link Validation**
   - Ensure all deal links include `sdtrk=bfsheet` parameter
   - Verify links open correctly

## Questions?

- Open an issue for general questions
- Tag maintainers for urgent matters

## Recognition

Contributors will be recognized in:
- GitHub contributors list
- Release notes for significant contributions

Thank you for helping make this project better! 🎉
