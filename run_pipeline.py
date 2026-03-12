#!/usr/bin/env python3
"""
Master Pipeline Orchestration Script

This script orchestrates the entire synonym generation and annotation workflow
in three phases: Setup, Processing, and Annotation.

Usage:
    python run_pipeline.py
"""
import os
import sys
import subprocess
import time
import signal


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_phase_header(phase_name):
    """Print a formatted phase header"""
    print(f"\n{'='*60}")
    print(f"{Colors.HEADER}{Colors.BOLD}PHASE: {phase_name}{Colors.ENDC}")
    print(f"{'='*60}\n")


def print_step(step_name):
    """Print a formatted step name"""
    print(f"{Colors.OKCYAN}▶ {step_name}{Colors.ENDC}")


def print_success(message):
    """Print a success message"""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_error(message):
    """Print an error message"""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


def print_warning(message):
    """Print a warning message"""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")


def wait_for_user(message):
    """Wait for user to press Enter to continue"""
    print(f"\n{Colors.WARNING}{Colors.BOLD}{message}{Colors.ENDC}")
    input(f"{Colors.OKCYAN}Press Enter to continue...{Colors.ENDC} ")
    print()


def run_command(command, description, background=False, shell=False):
    """
    Run a command and handle its output
    
    Args:
        command: Command to run (string or list)
        description: Human-readable description of the command
        background: If True, run in background and return process
        shell: If True, run command in shell
    
    Returns:
        Process object if background=True, else None
    """
    print_step(description)
    
    try:
        if background:
            # Start process in background
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=shell
            )
            print_success(f"Started in background (PID: {process.pid})")
            return process
        else:
            # Run and wait for completion
            result = subprocess.run(
                command,
                check=True,
                shell=shell,
                text=True
            )
            print_success(f"{description} completed")
            return None
            
    except subprocess.CalledProcessError as e:
        print_error(f"{description} failed with exit code {e.returncode}")
        raise
    except Exception as e:
        print_error(f"{description} failed: {str(e)}")
        raise


def check_appium_running():
    """Check if Appium server is already running"""
    ##TODO: Make the check more robust by looking for the actual process instead of just port usage
    try:
        result = subprocess.run(
            ["lsof", "-i", ":4723"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except:
        return False


def start_appium_server():
    """Start the Appium server"""
    if check_appium_running():
        print_warning("Appium server is already running on port 4723")
        return None
    
    print_step("Starting Appium server")
    
    try:
        # Start Appium in background
        process = subprocess.Popen(
            ["appium"],# runs appium server with default settings (port 4723)
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a bit for server to start
        time.sleep(3) #Reduced from 5 seconds to 3 seconds to speed up the pipeline, can be adjusted if needed
        
        # Check if it's running
        if check_appium_running():
            print_success(f"Appium server started (PID: {process.pid})")
            return process
        else:
            print_error("Appium server failed to start")
            return None
            
    except FileNotFoundError:
        print_error("Appium not found. Please install it with: npm install -g appium")
        raise
    except Exception as e:
        print_error(f"Failed to start Appium: {str(e)}")
        raise


def stop_appium_server(process):
    """Stop the Appium server"""
    if process:
        print_step("Stopping Appium server")
        process.terminate()
        try:
            process.wait(timeout=10)
            print_success("Appium server stopped")
        except subprocess.TimeoutExpired:
            print_warning("Appium server didn't stop gracefully, killing it")
            process.kill()
        except Exception as e:
            print_error(f"Failed to stop Appium server: {str(e)}")


def setup_phase():
    """Execute the setup phase"""
    print_phase_header("1. SETUP")
    
    appium_process = None
    
    try:
        # Step 1: Start Appium server
        appium_process = start_appium_server()
        
        # Step 2: Execute main.go with --setup flag
        run_command(
            ["go", "run", "main.go", "--setup"],
            "Running main.go (setup mode - translation and conversion)"
        )
        
        # Step 3: Run test automation
        run_command(
            ["python", "test_automation/android_test/test_mercari_search.py"],
            "Running search tests"
        )
        
        print_success("Setup phase completed successfully!")
        
        # Wait for user before proceeding
        wait_for_user("⏸  Waiting for BigQuery data. Please prepare the data.")
        
        return appium_process
        
    except Exception as e:
        print_error(f"Setup phase failed: {str(e)}")
        if appium_process:
            stop_appium_server(appium_process)
        raise


def processing_phase():
    """Execute the processing phase"""
    print_phase_header("2. PROCESSING")
    
    try:
        # Step 1: Execute BigQuery processing in main.go
        run_command(
            ["go", "run", "main.go", "--process"],
            "Processing BigQuery data"
        )
        
        # Step 2: Run synonyms analyzer
        run_command(
            ["python", "BigQueryOutputAnalyzer/synonyms.py"],
            "Analyzing BigQuery output"
        )
        
        print_success("Processing phase completed successfully!")
        
        # Wait for user verification
        wait_for_user("⏸  Please verify the BigQueryOutput directory.")
        
    except Exception as e:
        print_error(f"Processing phase failed: {str(e)}")
        raise


def annotation_phase():
    """Execute the annotation phase"""
    print_phase_header("3. ANNOTATION")
    start_appium_server()  # Ensure Appium is running for annotation phase
      
    print_success("Please run the (Annotator/annotator_helper_script.py) annotation script separately to annotate the results. This is a manual step that requires human judgment.")
    wait_for_user("⏸  After completing annotation, press Enter to finish the pipeline.")
    stop_appium_server(None)  # Stop Appium server after annotation
  


def main():
    """Main orchestration function"""
    print(f"{Colors.BOLD}{Colors.HEADER}")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║   Synonym Generation & Annotation Pipeline              ║")
    print("║   Three-Phase Workflow Orchestration                     ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")
    
    # Get the script directory and change to project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"Working directory: {script_dir}\n")
    
    appium_process = None
    
    try:
        # Phase 1: Setup
        appium_process = setup_phase()
        
        # Phase 2: Processing
        processing_phase()
        
        # Phase 3: Annotation
        annotation_phase()
        
        # All phases completed
        print(f"\n{'='*60}")
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ ALL PHASES COMPLETED SUCCESSFULLY!{Colors.ENDC}")
        print(f"{'='*60}\n")
        
    except KeyboardInterrupt:
        print_warning("\n\nPipeline interrupted by user")
        sys.exit(1)
        
    except Exception as e:
        print_error(f"\n\nPipeline failed: {str(e)}")
        sys.exit(1)
        
    finally:
        # Clean up: Stop Appium server
        if appium_process:
            stop_appium_server(appium_process)


if __name__ == "__main__":
    main()
