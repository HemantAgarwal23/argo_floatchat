#!/usr/bin/env python3
"""
Master ARGO Pipeline - Orchestrates the complete automated pipeline
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime
import logging

def setup_logging():
    """Setup logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)

class MasterPipeline:
    """Master pipeline orchestrator"""
    
    def __init__(self, year: int):
        self.year = year
        self.logger = setup_logging()
        
        # Pipeline state
        self.pipeline_state_file = Path(f"pipeline_state_{year}.json")
        self.scripts_dir = Path(__file__).parent
        
        # Pipeline steps
        self.steps = [
            {
                'name': 'download',
                'script': 'robust_download.py',
                'description': 'Download NetCDF files',
                'required': True
            },
            {
                'name': 'retry_failed',
                'script': 'retry_failed_downloads.py',
                'description': 'Retry failed downloads',
                'required': False
            },
            {
                'name': 'verify',
                'script': 'verify_downloads.py',
                'description': 'Verify downloaded files',
                'required': True
            },
            {
                'name': 'process',
                'script': 'process_data.py',
                'description': 'Process data into structured format',
                'required': True
            },
            {
                'name': 'deliverables',
                'script': 'create_deliverables.py',
                'description': 'Create final deliverables',
                'required': True
            }
        ]
        
        # Load previous state
        self.load_state()
    
    def load_state(self):
        """Load pipeline state"""
        if self.pipeline_state_file.exists():
            try:
                with open(self.pipeline_state_file, 'r') as f:
                    self.state = json.load(f)
                self.logger.info(f"📋 Loaded pipeline state: {self.state.get('current_step', 'start')}")
            except Exception as e:
                self.logger.warning(f"⚠️ Could not load pipeline state: {e}")
                self.state = {'current_step': 'start', 'completed_steps': []}
        else:
            self.state = {'current_step': 'start', 'completed_steps': []}
    
    def save_state(self):
        """Save pipeline state"""
        self.state['last_updated'] = datetime.now().isoformat()
        with open(self.pipeline_state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def run_script(self, script_name: str, description: str) -> bool:
        """Run a pipeline script"""
        self.logger.info(f"🚀 Running {description}...")
        
        script_path = self.scripts_dir / script_name
        if not script_path.exists():
            self.logger.error(f"❌ Script not found: {script_path}")
            return False
        
        try:
            # Run the script with real-time output
            result = subprocess.run([
                sys.executable, str(script_path), str(self.year)
            ], text=True)
            
            if result.returncode == 0:
                self.logger.info(f"✅ {description} completed successfully")
                return True
            else:
                self.logger.error(f"❌ {description} failed")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Failed to run {script_name}: {e}")
            return False
    
    def check_step_requirements(self, step_name: str) -> bool:
        """Check if step requirements are met"""
        if step_name == 'download':
            # For download, we can always proceed (it will check for existing files internally)
            return True
        
        elif step_name == 'retry_failed':
            # Check if failed downloads file exists
            failed_file = Path(f"failed_downloads_{self.year}.txt")
            return failed_file.exists()
        
        elif step_name == 'verify':
            # Check if download exists
            download_dir = Path("data/raw") / str(self.year)
            if download_dir.exists():
                nc_files = list(download_dir.rglob("*.nc"))
                if nc_files:
                    self.logger.info(f"📁 Found {len(nc_files)} files to verify")
                    return True
            self.logger.warning("⚠️ No files found to verify - skipping verification step")
            return False
        
        elif step_name == 'process':
            # Check if verification exists OR if we have raw files to process
            verification_file = Path(f"download_verification_{self.year}.json")
            if verification_file.exists():
                return True
            
            # If no verification file, check if we have raw files
            download_dir = Path("data/raw") / str(self.year)
            if download_dir.exists():
                nc_files = list(download_dir.rglob("*.nc"))
                if nc_files:
                    self.logger.info(f"📁 Found {len(nc_files)} files to process (no verification file)")
                    return True
            
            return False
        
        elif step_name == 'deliverables':
            # Check if processed data exists
            csv_file = Path("data/processed") / f"argo_data_{self.year}.csv"
            return csv_file.exists()
        
        return True
    
    def run_pipeline(self):
        """Run the complete pipeline"""
        self.logger.info(f"🚀 Starting Master ARGO Pipeline for {self.year}")
        self.logger.info("=" * 50)
        
        # Find starting point
        start_index = 0
        for i, step in enumerate(self.steps):
            if step['name'] == self.state.get('current_step', 'start'):
                start_index = i
                break
        
        # Run each step
        for i, step in enumerate(self.steps[start_index:], start_index):
            step_name = step['name']
            script_name = step['script']
            description = step['description']
            required = step['required']
            
            self.logger.info(f"\n📋 Step {i+1}/{len(self.steps)}: {description}")
            
            # Check if step is already completed
            if step_name in self.state.get('completed_steps', []):
                self.logger.info(f"✅ {description} already completed - skipping")
                continue
            
            # Check requirements
            if not self.check_step_requirements(step_name):
                if required:
                    self.logger.error(f"❌ Requirements not met for {description}")
                    self.logger.error("💡 Please run previous steps first")
                    return False
                else:
                    self.logger.info(f"⚠️ Requirements not met for {description} - skipping")
                    continue
            
            # Run the step
            success = self.run_script(script_name, description)
            
            if success:
                # Mark step as completed
                if 'completed_steps' not in self.state:
                    self.state['completed_steps'] = []
                self.state['completed_steps'].append(step_name)
                self.state['current_step'] = step_name
                self.save_state()
                
                self.logger.info(f"✅ {description} completed successfully")
            else:
                if required:
                    self.logger.error(f"❌ {description} failed - pipeline stopped")
                    return False
                else:
                    self.logger.warning(f"⚠️ {description} failed - continuing with next step")
        
        # Pipeline completed
        self.logger.info("\n🎉 Master Pipeline Completed Successfully!")
        self.logger.info("📁 Check the following directories for outputs:")
        self.logger.info(f"  - Raw data: data/raw/{self.year}/")
        self.logger.info(f"  - Processed data: data/processed/")
        self.logger.info(f"  - Deliverables: data/deliverables/")
        
        return True
    
    def reset_pipeline(self):
        """Reset pipeline state"""
        if self.pipeline_state_file.exists():
            self.pipeline_state_file.unlink()
        self.state = {'current_step': 'start', 'completed_steps': []}
        self.logger.info("🔄 Pipeline state reset")
    
    def get_pipeline_status(self):
        """Get current pipeline status"""
        self.logger.info(f"📋 Pipeline Status for {self.year}")
        self.logger.info("=" * 30)
        
        for i, step in enumerate(self.steps):
            step_name = step['name']
            description = step['description']
            
            if step_name in self.state.get('completed_steps', []):
                status = "✅ Completed"
            elif step_name == self.state.get('current_step'):
                status = "🔄 In Progress"
            else:
                status = "⏳ Pending"
            
            self.logger.info(f"  {i+1}. {description}: {status}")
        
        return self.state

def main():
    """Main function"""
    logger = setup_logging()
    
    print("🚀 Master ARGO Pipeline")
    print("=" * 30)
    print("This pipeline will:")
    print("1. Download NetCDF files (with retry on failure)")
    print("2. Verify downloaded files")
    print("3. Process data into structured format")
    print("4. Create final deliverables")
    print("=" * 30)
    
    # Get year from user
    year = input("Enter year to process (e.g., 2021): ").strip()
    if not year.isdigit():
        print("❌ Please enter a valid year")
        return
    
    year = int(year)
    
    # Create master pipeline
    pipeline = MasterPipeline(year=year)
    
    # Check if pipeline already exists
    if pipeline.state.get('completed_steps'):
        logger.info(f"📋 Found existing pipeline for {year}")
        logger.info("Current status:")
        pipeline.get_pipeline_status()
        
        choice = input("\nWhat would you like to do?\n1. Continue from where it left off\n2. Reset and start fresh\n3. Just show status\nEnter choice (1/2/3): ").strip()
        
        if choice == '2':
            pipeline.reset_pipeline()
        elif choice == '3':
            return True
    
    # Run pipeline
    success = pipeline.run_pipeline()
    
    if success:
        logger.info("🎉 Pipeline completed successfully!")
        logger.info("✅ All deliverables are ready")
    else:
        logger.error("❌ Pipeline failed")
        logger.info("💡 Check the logs for details")
        logger.info("💡 You can run the pipeline again to continue from where it left off")
    
    return success

if __name__ == "__main__":
    main()
