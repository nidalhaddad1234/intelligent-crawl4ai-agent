#!/usr/bin/env python3
"""
Docker Infrastructure Test Suite
Comprehensive testing for the Intelligent Crawl4AI Agent Docker setup
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional


class DockerTester:
    """Test Docker infrastructure and container functionality"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.docker_compose_file = self.project_root / "docker-compose.yml"
        self.dockerfile_agent = self.project_root / "docker" / "Dockerfile.agent"
        
    def run_command(self, cmd: List[str], capture_output: bool = True, timeout: int = 60) -> subprocess.CompletedProcess:
        """Run a command with error handling"""
        try:
            print(f"🔧 Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                cwd=self.project_root
            )
            return result
        except subprocess.TimeoutExpired:
            print(f"❌ Command timed out after {timeout}s: {' '.join(cmd)}")
            raise
        except Exception as e:
            print(f"❌ Command failed: {e}")
            raise
    
    def test_dockerfile_syntax(self) -> bool:
        """Test Dockerfile syntax and structure"""
        print("\n🧪 Testing Dockerfile Syntax")
        print("=" * 50)
        
        try:
            # Check if Dockerfile exists
            if not self.dockerfile_agent.exists():
                print(f"❌ Dockerfile not found: {self.dockerfile_agent}")
                return False
            
            print(f"✅ Dockerfile found: {self.dockerfile_agent}")
            
            # Validate Dockerfile content
            dockerfile_content = self.dockerfile_agent.read_text()
            
            # Check for required components
            required_components = [
                "FROM python:3.11-slim",
                "WORKDIR /app",
                "COPY requirements.txt",
                "RUN pip install",
                "COPY src/",
                "EXPOSE 8811",
                "HEALTHCHECK",
                "ENTRYPOINT"
            ]
            
            missing_components = []
            for component in required_components:
                if component not in dockerfile_content:
                    missing_components.append(component)
            
            if missing_components:
                print(f"❌ Missing Dockerfile components: {missing_components}")
                return False
            
            print("✅ All required Dockerfile components present")
            
            # Check for multi-stage build
            if "as base" in dockerfile_content and "as production" in dockerfile_content:
                print("✅ Multi-stage build structure detected")
            else:
                print("⚠️  Single-stage build (consider multi-stage for optimization)")
            
            return True
            
        except Exception as e:
            print(f"❌ Dockerfile validation failed: {e}")
            return False
    
    def test_docker_build(self) -> bool:
        """Test Docker image building"""
        print("\n🏗️  Testing Docker Build")
        print("=" * 50)
        
        try:
            # Build production image
            print("📦 Building production image...")
            build_cmd = [
                "docker", "build",
                "--target", "production",
                "-t", "intelligent-crawl4ai:test",
                "-f", "docker/Dockerfile.agent",
                "."
            ]
            
            result = self.run_command(build_cmd, capture_output=False, timeout=300)
            
            if result.returncode != 0:
                print(f"❌ Docker build failed with exit code {result.returncode}")
                return False
            
            print("✅ Docker build completed successfully")
            
            # Check if image was created
            inspect_cmd = ["docker", "inspect", "intelligent-crawl4ai:test"]
            result = self.run_command(inspect_cmd)
            
            if result.returncode == 0:
                print("✅ Docker image created and accessible")
                
                # Parse image info
                image_info = json.loads(result.stdout)[0]
                size_mb = image_info['Size'] / (1024 * 1024)
                print(f"📏 Image size: {size_mb:.1f} MB")
                
                return True
            else:
                print("❌ Docker image not found after build")
                return False
                
        except Exception as e:
            print(f"❌ Docker build test failed: {e}")
            return False
    
    def test_container_startup(self) -> bool:
        """Test container startup and basic functionality"""
        print("\n🚀 Testing Container Startup")
        print("=" * 50)
        
        container_name = "intelligent-crawl4ai-test"
        
        try:
            # Clean up any existing test container
            cleanup_cmd = ["docker", "rm", "-f", container_name]
            self.run_command(cleanup_cmd)
            
            # Start container in background
            print("🔄 Starting test container...")
            run_cmd = [
                "docker", "run",
                "--name", container_name,
                "--detach",
                "-p", "8811:8811",
                "-e", "MCP_SERVER_HOST=0.0.0.0",
                "-e", "MCP_SERVER_PORT=8811",
                "-e", "APP_ENV=test",
                "-e", "LOG_LEVEL=INFO",
                "-e", "DATABASE_TYPE=sqlite",
                "intelligent-crawl4ai:test"
            ]
            
            result = self.run_command(run_cmd)
            
            if result.returncode != 0:
                print(f"❌ Container failed to start: {result.stderr}")
                return False
            
            container_id = result.stdout.strip()
            print(f"✅ Container started: {container_id[:12]}")
            
            # Wait for startup
            print("⏳ Waiting for container to initialize...")
            time.sleep(10)
            
            # Check container status
            status_cmd = ["docker", "ps", "--filter", f"name={container_name}", "--format", "{{.Status}}"]
            result = self.run_command(status_cmd)
            
            if "Up" not in result.stdout:
                print(f"❌ Container not running: {result.stdout}")
                
                # Get logs for debugging
                logs_cmd = ["docker", "logs", container_name]
                logs_result = self.run_command(logs_cmd)
                print(f"📋 Container logs:\n{logs_result.stdout}\n{logs_result.stderr}")
                
                return False
            
            print("✅ Container is running")
            
            # Test health check
            health_cmd = ["docker", "exec", container_name, "python", "healthcheck.py"]
            result = self.run_command(health_cmd, timeout=30)
            
            if result.returncode == 0:
                print("✅ Health check passed")
                return True
            else:
                print(f"❌ Health check failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Container startup test failed: {e}")
            return False
        
        finally:
            # Clean up test container
            cleanup_cmd = ["docker", "rm", "-f", container_name]
            self.run_command(cleanup_cmd)
    
    def test_docker_compose_validation(self) -> bool:
        """Test docker-compose.yml validation"""
        print("\n🐳 Testing Docker Compose Configuration")
        print("=" * 50)
        
        try:
            if not self.docker_compose_file.exists():
                print(f"❌ docker-compose.yml not found: {self.docker_compose_file}")
                return False
            
            print("✅ docker-compose.yml found")
            
            # Validate compose file syntax
            validate_cmd = ["docker-compose", "config"]
            result = self.run_command(validate_cmd)
            
            if result.returncode != 0:
                print(f"❌ docker-compose.yml validation failed:\n{result.stderr}")
                return False
            
            print("✅ docker-compose.yml syntax is valid")
            
            # Check for required services
            compose_content = self.docker_compose_file.read_text()
            required_services = [
                "intelligent-agent",
                "chromadb",
                "ollama",
                "redis",
                "postgres"
            ]
            
            missing_services = []
            for service in required_services:
                if f"{service}:" not in compose_content:
                    missing_services.append(service)
            
            if missing_services:
                print(f"⚠️  Missing recommended services: {missing_services}")
            else:
                print("✅ All recommended services present")
            
            return True
            
        except Exception as e:
            print(f"❌ Docker Compose validation failed: {e}")
            return False
    
    def test_environment_variables(self) -> bool:
        """Test environment variable configuration"""
        print("\n🌍 Testing Environment Configuration")
        print("=" * 50)
        
        try:
            # Check if .env.example exists
            env_example = self.project_root / ".env.example"
            if env_example.exists():
                print("✅ .env.example found")
                
                env_content = env_example.read_text()
                
                # Check for critical environment variables
                critical_vars = [
                    "OLLAMA_URL",
                    "CHROMADB_URL",
                    "REDIS_URL",
                    "POSTGRES_URL",
                    "MCP_SERVER_HOST",
                    "MCP_SERVER_PORT"
                ]
                
                missing_vars = []
                for var in critical_vars:
                    if var not in env_content:
                        missing_vars.append(var)
                
                if missing_vars:
                    print(f"⚠️  Missing environment variables in .env.example: {missing_vars}")
                else:
                    print("✅ All critical environment variables documented")
                
            else:
                print("⚠️  .env.example not found")
            
            return True
            
        except Exception as e:
            print(f"❌ Environment configuration test failed: {e}")
            return False
    
    def test_file_permissions(self) -> bool:
        """Test file permissions in Docker context"""
        print("\n🔐 Testing File Permissions")
        print("=" * 50)
        
        try:
            # Check entrypoint script permissions
            entrypoint_script = self.project_root / "docker" / "agent-entrypoint.sh"
            if entrypoint_script.exists():
                # Check if file is executable
                if os.access(entrypoint_script, os.X_OK):
                    print("✅ Entrypoint script is executable")
                else:
                    print("⚠️  Entrypoint script may need execute permissions")
            else:
                print("❌ Entrypoint script not found")
                return False
            
            # Check health check script permissions
            healthcheck_script = self.project_root / "docker" / "agent-healthcheck.py"
            if healthcheck_script.exists():
                if os.access(healthcheck_script, os.X_OK):
                    print("✅ Health check script is executable")
                else:
                    print("⚠️  Health check script may need execute permissions")
            else:
                print("❌ Health check script not found")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ File permissions test failed: {e}")
            return False
    
    async def run_all_tests(self) -> bool:
        """Run comprehensive Docker infrastructure tests"""
        print("🎯 Docker Infrastructure Test Suite")
        print("🚀 Testing Intelligent Crawl4AI Agent Docker Setup")
        print("=" * 70)
        
        tests = [
            ("Dockerfile Syntax", self.test_dockerfile_syntax),
            ("Environment Variables", self.test_environment_variables),
            ("File Permissions", self.test_file_permissions),
            ("Docker Compose Validation", self.test_docker_compose_validation),
            ("Docker Build", self.test_docker_build),
            ("Container Startup", self.test_container_startup),
        ]
        
        passed_tests = 0
        failed_tests = []
        
        for test_name, test_func in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            
            try:
                if test_func():
                    print(f"✅ {test_name} PASSED")
                    passed_tests += 1
                else:
                    print(f"❌ {test_name} FAILED")
                    failed_tests.append(test_name)
            except Exception as e:
                print(f"❌ {test_name} ERROR: {e}")
                failed_tests.append(test_name)
        
        # Summary
        print("\n" + "="*70)
        print("📊 TEST SUMMARY")
        print("="*70)
        print(f"✅ Passed: {passed_tests}/{len(tests)}")
        print(f"❌ Failed: {len(failed_tests)}/{len(tests)}")
        
        if failed_tests:
            print(f"📋 Failed tests: {', '.join(failed_tests)}")
            print("\n🔧 Next steps:")
            print("   1. Review failed test output above")
            print("   2. Fix any configuration issues")
            print("   3. Re-run tests to verify fixes")
            return False
        else:
            print("\n🎉 All tests passed! Docker infrastructure is ready.")
            print("\n🚀 Ready for deployment:")
            print("   • docker-compose up -d")
            print("   • docker build -t intelligent-crawl4ai .")
            print("   • docker run intelligent-crawl4ai")
            return True


async def main():
    """Main test execution"""
    try:
        tester = DockerTester()
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
