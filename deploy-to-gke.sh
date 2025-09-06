#!/bin/bash

# Bank of Anthos Deployment Script for GKE
echo "🚀 Deploying Bank of Anthos with Fraud Detection to GKE"
echo "======================================================="

# Set variables
PROJECT_ID="gke-boa-471214"
CLUSTER_NAME="bank-of-anthos"
ZONE="us-central1-a"

echo "📋 Project: $PROJECT_ID"
echo "🎯 Cluster: $CLUSTER_NAME"
echo "🌍 Zone: $ZONE"

# Get cluster credentials
echo ""
echo "🔐 Getting cluster credentials..."
gcloud container clusters get-credentials $CLUSTER_NAME --zone $ZONE --project $PROJECT_ID

if [ $? -ne 0 ]; then
    echo "❌ Failed to get cluster credentials. Is the cluster ready?"
    exit 1
fi

echo "✅ Connected to cluster"

# Deploy ConfigMaps and Secrets first
echo ""
echo "⚙️  Deploying configuration..."
kubectl apply -f kubernetes-manifests/config.yaml
kubectl apply -f kubernetes-manifests/demo-data-config.yaml
kubectl apply -f kubernetes-manifests/jwt-secret.yaml
kubectl apply -f kubernetes-manifests/gemini-secret.yaml

# Deploy databases first
echo ""
echo "💾 Deploying databases..."
kubectl apply -f kubernetes-manifests/accounts-db.yaml
kubectl apply -f kubernetes-manifests/ledger-db.yaml

# Wait for databases to be ready
echo "⏳ Waiting for databases to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/accounts-db
kubectl wait --for=condition=available --timeout=300s deployment/postgres

# Deploy backend services
echo ""
echo "🔧 Deploying backend services..."
kubectl apply -f kubernetes-manifests/userservice.yaml
kubectl apply -f kubernetes-manifests/contacts.yaml
kubectl apply -f kubernetes-manifests/balance-reader.yaml
kubectl apply -f kubernetes-manifests/ledger-writer.yaml
kubectl apply -f kubernetes-manifests/transaction-history.yaml

# Wait for backend services
echo "⏳ Waiting for backend services..."
kubectl wait --for=condition=available --timeout=300s deployment/userservice
kubectl wait --for=condition=available --timeout=300s deployment/contacts
kubectl wait --for=condition=available --timeout=300s deployment/balancereader
kubectl wait --for=condition=available --timeout=300s deployment/ledgerwriter
kubectl wait --for=condition=available --timeout=300s deployment/transactionhistory

# Deploy fraud detection service
echo ""
echo "🔍 Deploying fraud detection service..."
kubectl apply -f kubernetes-manifests/frauddetection.yaml

# Wait for fraud detection
echo "⏳ Waiting for fraud detection service..."
kubectl wait --for=condition=available --timeout=300s deployment/frauddetection

# Deploy frontend
echo ""
echo "🖥️  Deploying frontend..."
kubectl apply -f kubernetes-manifests/frontend.yaml

# Wait for frontend
echo "⏳ Waiting for frontend..."
kubectl wait --for=condition=available --timeout=300s deployment/frontend

# Deploy load generator (optional)
echo ""
echo "📊 Deploying load generator..."
kubectl apply -f kubernetes-manifests/loadgenerator.yaml

# Get the external IP
echo ""
echo "🌐 Getting external access information..."

# Create LoadBalancer service for frontend if it doesn't exist
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: frontend-external
  labels:
    application: bank-of-anthos
spec:
  type: LoadBalancer
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
EOF

echo ""
echo "⏳ Waiting for external IP assignment..."
echo "This may take a few minutes..."

# Wait for external IP
for i in {1..30}; do
    EXTERNAL_IP=$(kubectl get svc frontend-external -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)
    if [ -n "$EXTERNAL_IP" ] && [ "$EXTERNAL_IP" != "null" ]; then
        break
    fi
    echo "⏳ Waiting for IP... (attempt $i/30)"
    sleep 10
done

echo ""
echo "🎉 Deployment Complete!"
echo "======================"

if [ -n "$EXTERNAL_IP" ] && [ "$EXTERNAL_IP" != "null" ]; then
    echo "🌐 Frontend URL: http://$EXTERNAL_IP"
    echo "📱 Access your Bank of Anthos app at: http://$EXTERNAL_IP"
else
    echo "⚠️  External IP not ready yet. Check with:"
    echo "   kubectl get svc frontend-external"
fi

echo ""
echo "📊 Cluster Status:"
kubectl get pods
echo ""
echo "🔧 Services:"
kubectl get svc

echo ""
echo "💡 Useful commands:"
echo "   kubectl get pods                    # Check pod status"
echo "   kubectl get svc                     # Check services"
echo "   kubectl logs -l app=frauddetection  # Check fraud detection logs"
echo "   kubectl get svc frontend-external   # Get frontend IP"
