#!/usr/bin/env python3
"""
Verification script for LabelMe Augmentor installation.

This script verifies that all components are properly installed and working.
"""

import sys
from pathlib import Path


def check_imports():
    """Verify all modules can be imported."""
    print("=" * 70)
    print("CHECKING IMPORTS")
    print("=" * 70)
    
    modules = [
        "labelme_augmentor",
        "labelme_augmentor.core",
        "labelme_augmentor.io",
        "labelme_augmentor.validation",
        "labelme_augmentor.transforms",
        "labelme_augmentor.visualization",
        "labelme_augmentor.config",
        "labelme_augmentor.utils",
    ]
    
    failed = []
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            failed.append(module)
    
    return len(failed) == 0


def check_version():
    """Check package version."""
    print("\n" + "=" * 70)
    print("CHECKING VERSION")
    print("=" * 70)
    
    try:
        from labelme_augmentor import __version__
        print(f"✅ Version: {__version__}")
        return True
    except Exception as e:
        print(f"❌ Failed to get version: {e}")
        return False


def check_config_validation():
    """Check Pydantic config validation."""
    print("\n" + "=" * 70)
    print("CHECKING CONFIG VALIDATION")
    print("=" * 70)
    
    try:
        from labelme_augmentor.config import MainConfig
        
        # Test minimal valid config
        config = MainConfig(
            paths={"input_json_dir": "/tmp", "output_dir": "/tmp/out"}
        )
        print("✅ Pydantic config validation works")
        print(f"   Default seed: {config.general.seed}")
        return True
    except Exception as e:
        print(f"❌ Config validation failed: {e}")
        return False


def check_cli():
    """Check CLI entry point."""
    print("\n" + "=" * 70)
    print("CHECKING CLI")
    print("=" * 70)
    
    try:
        from labelme_augmentor.cli import main
        print("✅ CLI module importable")
        return True
    except Exception as e:
        print(f"❌ CLI check failed: {e}")
        return False


def check_tests():
    """Check if tests are available."""
    print("\n" + "=" * 70)
    print("CHECKING TESTS")
    print("=" * 70)
    
    test_dir = Path("tests")
    if test_dir.exists():
        test_files = list(test_dir.rglob("test_*.py"))
        print(f"✅ Found {len(test_files)} test files")
        for test_file in test_files[:5]:
            print(f"   - {test_file}")
        if len(test_files) > 5:
            print(f"   ... and {len(test_files) - 5} more")
        return True
    else:
        print("❌ Tests directory not found")
        return False


def check_documentation():
    """Check if documentation exists."""
    print("\n" + "=" * 70)
    print("CHECKING DOCUMENTATION")
    print("=" * 70)
    
    docs = ["README.md", "QUICKSTART.md", "MIGRATION_GUIDE.md", "CHANGELOG.md"]
    found = []
    missing = []
    
    for doc in docs:
        if Path(doc).exists():
            found.append(doc)
            print(f"✅ {doc}")
        else:
            missing.append(doc)
            print(f"❌ {doc} not found")
    
    return len(missing) == 0


def check_examples():
    """Check if examples exist."""
    print("\n" + "=" * 70)
    print("CHECKING EXAMPLES")
    print("=" * 70)
    
    examples_dir = Path("examples")
    if examples_dir.exists():
        examples = list(examples_dir.glob("*.py"))
        print(f"✅ Found {len(examples)} example files")
        for example in examples:
            print(f"   - {example}")
        return True
    else:
        print("❌ Examples directory not found")
        return False


def check_ci_cd():
    """Check if CI/CD is configured."""
    print("\n" + "=" * 70)
    print("CHECKING CI/CD")
    print("=" * 70)
    
    workflows_dir = Path(".github/workflows")
    if workflows_dir.exists():
        workflows = list(workflows_dir.glob("*.yml"))
        print(f"✅ Found {len(workflows)} workflow files")
        for workflow in workflows:
            print(f"   - {workflow}")
        return True
    else:
        print("❌ GitHub workflows not found")
        return False


def main():
    """Run all verification checks."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  LabelMe Augmentor - Installation Verification".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")
    print("\n")
    
    checks = [
        ("Imports", check_imports),
        ("Version", check_version),
        ("Config Validation", check_config_validation),
        ("CLI", check_cli),
        ("Tests", check_tests),
        ("Documentation", check_documentation),
        ("Examples", check_examples),
        ("CI/CD", check_ci_cd),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} check crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print("\n" + "-" * 70)
    print(f"Result: {passed}/{total} checks passed")
    print("-" * 70)
    
    if passed == total:
        print("\n🎉 All checks passed! Installation is complete and working.")
        print("\nNext steps:")
        print("  1. Run tests: pytest")
        print("  2. Try examples: python examples/basic_usage.py")
        print("  3. Read docs: cat README.md")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
