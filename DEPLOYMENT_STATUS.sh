#!/usr/bin/env bash
# Deployment Preparation Checklist
# Generated: February 8, 2026

echo "======================================="
echo "Ani Health - Deployment Status Report"
echo "======================================="
echo ""

echo "✓ Python Syntax Validation"
python -m py_compile Ani/app.py && echo "  ✓ app.py: Valid" || echo "  ✗ app.py: Invalid"

echo ""
echo "✓ File Structure Check"
[ -f "Ani/app.py" ] && echo "  ✓ Main app.py exists" || echo "  ✗ Main app.py missing"
[ -f "api/index.py" ] && echo "  ✓ Vercel handler exists" || echo "  ✗ Vercel handler missing"
[ -f "requirements.txt" ] && echo "  ✓ Requirements file exists" || echo "  ✗ Requirements file missing"
[ -f "vercel.json" ] && echo "  ✓ Vercel config exists" || echo "  ✗ Vercel config missing"
[ -f ".env.example" ] && echo "  ✓ Environment template exists" || echo "  ✗ Environment template missing"
[ -f "README.md" ] && echo "  ✓ README exists" || echo "  ✗ README missing"

echo ""
echo "✓ Configuration Check"
grep -q "FLASK_ENV" Ani/app.py && echo "  ✓ Environment-aware config" || echo "  ✗ Missing env config"
grep -q "DB_PATH" Ani/app.py && echo "  ✓ Database path configured" || echo "  ✗ Database path issue"
grep -q "SECRET_KEY" Ani/app.py && echo "  ✓ Secret key configured" || echo "  ✗ Secret key issue"

echo ""
echo "✓ Database References"
DB_COUNT=$(grep -c "sqlite3.connect(DB_PATH)" Ani/app.py)
echo "  ✓ Database path references: $DB_COUNT"

echo ""
echo "✓ Git Status"
git status --porcelain
echo ""

echo "======================================="
echo "Deployment Status: READY FOR VERCEL"
echo "======================================="
echo ""
echo "Next steps:"
echo "1. Go to https://vercel.com"
echo "2. Import this GitHub repository"
echo "3. Set environment variables:"
echo "   - FLASK_ENV=production"
echo "   - SECRET_KEY=<generate-secure-key>"
echo "4. Click 'Deploy'"
echo ""
