import pytest
import os
import sys


def test_project_structure():
    """Test that the project structure is properly created."""
    # Test backend structure
    backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Check core directories exist
    assert os.path.exists(os.path.join(backend_root, "app"))
    assert os.path.exists(os.path.join(backend_root, "app", "core"))
    assert os.path.exists(os.path.join(backend_root, "app", "api"))
    assert os.path.exists(os.path.join(backend_root, "app", "db"))
    assert os.path.exists(os.path.join(backend_root, "app", "models"))
    assert os.path.exists(os.path.join(backend_root, "app", "services"))
    assert os.path.exists(os.path.join(backend_root, "app", "schemas"))
    assert os.path.exists(os.path.join(backend_root, "app", "repositories"))
    assert os.path.exists(os.path.join(backend_root, "tests"))
    
    # Check key files exist
    assert os.path.exists(os.path.join(backend_root, "app", "main.py"))
    assert os.path.exists(os.path.join(backend_root, "app", "core", "config.py"))
    assert os.path.exists(os.path.join(backend_root, "app", "core", "logging.py"))
    assert os.path.exists(os.path.join(backend_root, "app", "db", "session.py"))
    assert os.path.exists(os.path.join(backend_root, "requirements.txt"))
    assert os.path.exists(os.path.join(backend_root, "Dockerfile"))
    assert os.path.exists(os.path.join(backend_root, "alembic.ini"))
    assert os.path.exists(os.path.join(backend_root, ".env.example"))


def test_frontend_structure():
    """Test that the frontend structure is properly created."""
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    frontend_root = os.path.join(project_root, "frontend")
    
    if os.path.exists(frontend_root):
        # Check frontend structure
        assert os.path.exists(os.path.join(frontend_root, "src"))
        assert os.path.exists(os.path.join(frontend_root, "src", "pages"))
        assert os.path.exists(os.path.join(frontend_root, "package.json"))
        assert os.path.exists(os.path.join(frontend_root, "vite.config.js"))
        assert os.path.exists(os.path.join(frontend_root, "tailwind.config.js"))
        assert os.path.exists(os.path.join(frontend_root, "index.html"))


def test_config_files_exist():
    """Test that configuration files exist."""
    backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    assert os.path.exists(os.path.join(backend_root, ".env.example"))
    assert os.path.exists(os.path.join(backend_root, ".env.staging.example"))
    assert os.path.exists(os.path.join(backend_root, ".env.production.example"))
    assert os.path.exists(os.path.join(backend_root, "lightsail-deployment.sh"))
    assert os.path.exists(os.path.join(backend_root, "lightsail-container-setup.json"))
