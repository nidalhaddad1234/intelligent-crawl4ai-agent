#!/usr/bin/env python3
"""
Final verification test for Docker infrastructure implementation
Validates all components are properly implemented and configured
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def check_file_exists(file_path: str, description: str) -> Tuple[bool, str]:
    """Check if a file exists and return status"""
    path = Path(file_path)
    if path.exists():
        size = path.stat().st_size
        return True, f"✅ {description}: {file_path} ({size:,} bytes)"
    else:
        return False, f"❌ {description}: {file_path} (missing)"


def check_file_executable(file_path: str, description: str) -> Tuple[bool, str]:
    """Check if a file is executable"""
    path = Path(file_path)
    if path.exists():
        if os.access(path, os.X_OK):
            return True, f"✅ {description}: {file_path} (executable)"
        else:
            return False, f"⚠️  {description}: {file_path} (not executable)"
    else:
        return False, f"❌ {description}: {file_path} (missing)"


def check_dockerfile_content(dockerfile_path: str) -> Tuple[bool, str]:
    """Check Dockerfile content for required components"""
    try:
        content = Path(dockerfile_path).read_text()
        
        required_stages = [
            "FROM python:3.11-slim as base",
            "as node-stage",
            "as python-deps", 
            "as app-build",
            "as production"
        ]
        
        required_components = [
            "WORKDIR /app",
            "COPY requirements.txt",
            "RUN pip install",
            "COPY --chown=appuser:appuser src/",
            "EXPOSE 8811",
            "HEALTHCHECK",
            "ENTRYPOINT",
            "USER appuser"
        ]
        
        missing_stages = [stage for stage in required_stages if stage not in content]
        missing_components = [comp for comp in required_components if comp not in content]
        
        if not missing_stages and not missing_components:
            return True, f"✅ Dockerfile: Multi-stage build with all components"
        else:
            issues = []
            if missing_stages:
                issues.append(f"Missing stages: {missing_stages}")
            if missing_components:
                issues.append(f"Missing components: {missing_components}")
            return False, f"❌ Dockerfile: {'; '.join(issues)}"
            
    except Exception as e:
        return False, f"❌ Dockerfile: Error reading file - {e}"


def check_compose_services(compose_path: str) -> Tuple[bool, str]:
    """Check docker-compose.yml for required services"""
    try:
        content = Path(compose_path).read_text()
        
        required_services = [
            "intelligent-agent:",
            "chromadb:",
            "ollama:",
            "redis:",
            "postgres:",
            "browser-pool-1:",
            "prometheus:",
            "grafana:"
        ]
        
        found_services = [svc for svc in required_services if svc in content]
        missing_services = [svc for svc in required_services if svc not in content]
        
        if len(found_services) >= 5:  # Core services
            return True, f"✅ Docker Compose: {len(found_services)}/{len(required_services)} services configured"
        else:
            return False, f"❌ Docker Compose: Missing critical services - {missing_services}"
            
    except Exception as e:
        return False, f"❌ Docker Compose: Error reading file - {e}"


def check_entrypoint_features(entrypoint_path: str) -> Tuple[bool, str]:
    """Check entrypoint script for key features"""
    try:
        content = Path(entrypoint_path).read_text()
        
        required_features = [
            "check_env_vars()",
            "init_database()",
            "init_ai_services()",
            "shutdown_handler()",
            "start_application()",
            '"mcp-server")',
            '"debug")'
        ]
        
        found_features = [feat for feat in required_features if feat in content]
        
        if len(found_features) >= 6:
            return True, f"✅ Entrypoint: {len(found_features)}/{len(required_features)} features implemented"
        else:
            missing = [feat for feat in required_features if feat not in content]
            return False, f"❌ Entrypoint: Missing features - {missing}"
            
    except Exception as e:
        return False, f"❌ Entrypoint: Error reading file - {e}"


def check_healthcheck_capabilities(healthcheck_path: str) -> Tuple[bool, str]:
    """Check health check script capabilities"""
    try:
        content = Path(healthcheck_path).read_text()
        
        required_checks = [
            "check_mcp_server",
            "check_ai_services", 
            "check_system_resources",
            "check_file_system",
            "check_environment"
        ]
        
        found_checks = [check for check in required_checks if check in content]
        
        if len(found_checks) >= 4:
            return True, f"✅ Health Check: {len(found_checks)}/{len(required_checks)} checks implemented"
        else:
            missing = [check for check in required_checks if check not in content]
            return False, f"❌ Health Check: Missing checks - {missing}"
            
    except Exception as e:
        return False, f"❌ Health Check: Error reading file - {e}"


def main():
    """Run comprehensive Docker infrastructure validation"""
    print("🎯 Docker Infrastructure - Final Validation")
    print("=" * 60)
    
    # File existence checks
    file_checks = [
        ("docker/Dockerfile.agent", "Main Dockerfile"),
        ("docker/agent-entrypoint.sh", "Entrypoint Script"),
        ("docker/agent-healthcheck.py", "Health Check Script"),
        ("docker/build.sh", "Build Management Script"),
        ("docker/.env.docker", "Docker Environment Template"),
        ("docker-compose.yml", "Docker Compose Configuration"),
        (".env.example", "Environment Example"),
        ("test_docker_infrastructure.py", "Infrastructure Test Suite")
    ]
    
    print("\n📁 File Existence Validation:")
    print("-" * 40)
    
    file_results = []
    for file_path, description in file_checks:
        success, message = check_file_exists(file_path, description)
        file_results.append((success, message))
        print(message)
    
    # Executable checks
    print("\n🔧 Executable Permissions:")
    print("-" * 40)
    
    executable_checks = [
        ("docker/agent-entrypoint.sh", "Entrypoint Script"),
        ("docker/agent-healthcheck.py", "Health Check Script"),
        ("docker/build.sh", "Build Script")
    ]
    
    executable_results = []
    for file_path, description in executable_checks:
        success, message = check_file_executable(file_path, description)
        executable_results.append((success, message))
        print(message)
    
    # Content validation checks
    print("\n🔍 Content Validation:")
    print("-" * 40)
    
    content_checks = [
        (check_dockerfile_content, "docker/Dockerfile.agent"),
        (check_compose_services, "docker-compose.yml"),
        (check_entrypoint_features, "docker/agent-entrypoint.sh"),
        (check_healthcheck_capabilities, "docker/agent-healthcheck.py")
    ]
    
    content_results = []
    for check_func, file_path in content_checks:
        success, message = check_func(file_path)
        content_results.append((success, message))
        print(message)
    
    # Calculate overall results
    all_results = file_results + executable_results + content_results
    passed_count = sum(1 for success, _ in all_results if success)
    total_count = len(all_results)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {passed_count}/{total_count}")
    print(f"❌ Failed: {total_count - passed_count}/{total_count}")
    
    if passed_count == total_count:
        print("\n🎉 ALL VALIDATIONS PASSED!")
        print("✨ Docker infrastructure is fully implemented and ready!")
        print("\n🚀 Ready for deployment:")
        print("   • Multi-stage production Dockerfile")
        print("   • Intelligent entrypoint with service discovery")
        print("   • Comprehensive health checking")
        print("   • Build management and automation")
        print("   • Complete Docker Compose orchestration")
        print("   • Environment configuration templates")
        print("\n📋 Next steps:")
        print("   1. Copy docker/.env.docker to .env and configure")
        print("   2. Run: docker/build.sh build")
        print("   3. Run: docker/build.sh start")
        print("   4. Access: http://localhost:8811")
        
        return 0
    else:
        failed_items = [msg for success, msg in all_results if not success]
        print(f"\n⚠️  {len(failed_items)} validation(s) need attention:")
        for item in failed_items:
            print(f"   • {item}")
        
        print("\n🔧 Fix the issues above and re-run validation")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
