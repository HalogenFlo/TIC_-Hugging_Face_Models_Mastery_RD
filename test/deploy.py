import os
import subprocess
import time
from dotenv import load_dotenv
from google.cloud import aiplatform

# 1. Load configuration variables from .env file
load_dotenv()
key_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../gcp-key.json"))
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path

PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
REGION = os.environ.get("GCP_REGION", "us-central1")
BUCKET_URI = os.environ.get("GCP_BUCKET_URI")

if not PROJECT_ID or not BUCKET_URI:
    print("[ERROR] Please make sure GCP_PROJECT_ID and GCP_BUCKET_URI are configured in your .env file!")
    exit(1)

print("="*60)
print(" DEPLOYMENT CONFIGURATION DETAILS:")
print(f" - Project ID: {PROJECT_ID}")
print(f" - Region:     {REGION}")
print(f" - Bucket URI: {BUCKET_URI}")
print("="*60)

# Initialize Vertex AI SDK
aiplatform.init(project=PROJECT_ID, location=REGION)
print("[OK] Successfully initialized connection with Vertex AI SDK.\n")


def run_command(command, description):
    """Helper function to execute shell commands and handle logs."""
    print(f"[RUNNING] {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(f"[SUCCESS] {description} completed.\n")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to execute: {description}")
        print(f"Error details: {e.stderr}")
        raise e


# =====================================================================
# METHOD 1: DEPLOY VIA HUGGING FACE MODEL GARDEN (PRE-BUILT serving)
# =====================================================================
print("="*60)
print(" METHOD 1: HUGGING FACE MODEL GARDEN DEPLOYMENT")
print("="*60)

try:
    print("[1/3] Uploading Qwen base model from Model Garden to Model Registry...")
    model_garden = aiplatform.Model.upload(
        display_name="qwen-model-garden-production",
        serving_container_image_uri="us-docker.pkg.dev/deeplearning-platform-release/gcs-fuse/huggingface-text-generation-inference.1-3.py310",
        serving_container_environment_variables={
            "HF_MODEL_ID": "Qwen/Qwen2.5-0.5B-Instruct",
            "HF_TASK": "text-generation",
            "MAX_INPUT_LENGTH": "1024",
            "MAX_TOTAL_TOKENS": "2048"
        }
    )
    
    print("[2/3] Creating Endpoint for Model Garden...")
    endpoint_garden = aiplatform.Endpoint.create(display_name="qwen-garden-endpoint-prod")
    
    print("[3/3] Deploying model to Endpoint (Using CPU machine n1-standard-2)...")
    print("      Note: This process takes about 5-8 minutes to provision GCP hardware...")
    model_garden.deploy(
        endpoint=endpoint_garden,
        machine_type="n1-standard-2",
        min_replica_count=1,
        max_replica_count=1
    )
    print(f"[OK] Method 1 deployed successfully!")
    print(f"     Endpoint Resource Name: {endpoint_garden.resource_name}\n")
except Exception as e:
    print(f"[FAIL] Method 1 failed with error: {str(e)}\n")


# =====================================================================
# METHOD 2: DEPLOY VIA CUSTOM CONTAINER (YOUR FINE-TUNED QLORA)
# =====================================================================
print("="*60)
print(" METHOD 2: CUSTOM CONTAINER DEPLOYMENT (QLORA)")
print("="*60)

try:
    # 2.1 Copy local QLoRA weights to Cloud Storage Bucket
    run_command(
        f"gcloud storage cp -r ./notebook/qwen-2.5b-finetuned-qlora {BUCKET_URI}/qwen-2.5b-finetuned-qlora",
        "Uploading QLoRA weights to Google Cloud Storage"
    )

    # 2.2 Create Google Artifact Registry Repository
    run_command(
        f"gcloud artifacts repositories create custom-model-qwen --repository-format=docker --location={REGION} --description='Custom Model Repository for Qwen' || true",
        "Creating Artifact Registry Repository (if not exists)"
    )

    # 2.3 Configure Docker authentication with GCP
    run_command(
        f"gcloud auth configure-docker {REGION}-docker.pkg.dev --quiet",
        "Configuring Docker authentication with Google Artifact Registry"
    )

    # 2.4 Build custom Docker serving image
    run_command(
        "docker build -t custom-model-qwen:latest -f ./Dockerfile .",
        "Building Custom Serving Docker Image"
    )

    # 2.5 Tag and push Docker image to Cloud Repository
    image_tag = f"{REGION}-docker.pkg.dev/{PROJECT_ID}/custom-model-qwen/qwen-serving:v1"
    run_command(
        f"docker tag custom-model-qwen:latest {image_tag}",
        "Tagging Docker Image for Google Artifact Registry"
    )
    run_command(
        f"docker push {image_tag}",
        "Pushing Docker Image to Google Artifact Registry"
    )

    # 2.6 Register Custom Model in Vertex AI Model Registry
    print("[1/3] Uploading Custom Model with Serving Container to Model Registry...")
    model_custom = aiplatform.Model.upload(
        display_name="qwen-qlora-custom-prod",
        artifact_uri=f"{BUCKET_URI}/qwen-2.5b-finetuned-qlora",
        serving_container_image_uri=image_tag,
        serving_container_ports=[8000],
        serving_container_health_route="/health",
        serving_container_predict_route="/predict",
        serving_container_environment_variables={
            "GCS_URI": f"{BUCKET_URI}/qwen-2.5b-finetuned-qlora"
        }
    )

    # 2.7 Create Custom Endpoint
    print("[2/3] Creating Endpoint for Custom Model...")
    endpoint_custom = aiplatform.Endpoint.create(display_name="qwen-custom-endpoint-prod")

    # 2.8 Deploy Custom Model to Endpoint
    print("[3/3] Deploying Custom Model to Endpoint (Using CPU machine n1-standard-2)...")
    print("      Note: This process takes about 5-8 minutes...")
    model_custom.deploy(
        endpoint=endpoint_custom,
        machine_type="n1-standard-2",
        min_replica_count=1,
        max_replica_count=1
    )
    print(f"[OK] Method 2 deployed successfully!")
    print(f"     Endpoint Resource Name: {endpoint_custom.resource_name}\n")

    # =====================================================================
    # INFERENCE TEST (PREDICTION CHALLENGE)
    # =====================================================================
    print("="*60)
    print(" INFERENCE TEST (PREDICTION CHALLENGE)")
    print("="*60)
    print("[RUNNING] Sending validation request to Custom Endpoint...")
    response = endpoint_custom.predict(
        instances=["What is the capital of France?"]
    )
    print(f"[RESULT] Response from deployed model: {response.predictions}\n")

except Exception as e:
    print(f"[FAIL] Method 2 failed with error: {str(e)}\n")


# =====================================================================
# RESOURCE CLEAN UP (COST MINIMIZATION)
# =====================================================================
print("="*60)
print(" RESOURCE CLEAN UP (COST MINIMIZATION)")
print("="*60)
confirm = input("Do you want to clean up (delete) the active endpoints to avoid unexpected GCP bills? (y/n): ")

if confirm.lower() == 'y':
    try:
        if 'endpoint_custom' in locals():
            print("[CLEANING] Undeploying and deleting Custom Endpoint...")
            endpoint_custom.undeploy_all()
            endpoint_custom.delete()
            print("[SUCCESS] Custom Endpoint deleted.")
            
        if 'endpoint_garden' in locals():
            print("[CLEANING] Undeploying and deleting Garden Endpoint...")
            endpoint_garden.undeploy_all()
            endpoint_garden.delete()
            print("[SUCCESS] Garden Endpoint deleted.")
            
        print("[OK] Successfully cleaned up all cloud resources!")
    except Exception as e:
        print(f"[WARNING] An error occurred during clean up: {str(e)}")
else:
    print("[NOTICE] Endpoints are kept active. Please remember to delete them manually on Console to avoid charges!")
