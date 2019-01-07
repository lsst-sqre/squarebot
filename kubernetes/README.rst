####################
Kubernetes manifests
####################

These are Kubernetes manifests for SQuaRE Bot, Jr.

Deployment from scratch::

   kubectl apply -f sqrbot-jr-service.yaml
   kubectl apply -f sqrbot-jr-config.yaml
   kubectl apply -f sqrbot-jr-deployment.yaml
   kubectl apply -f sqrbot-jr-ingress.yaml

Resource manifests
==================

``sqrbot-jr-service.yaml``
   This is a ``Service`` called ``sqrbot-jr`` that receives traffic from the ingress and routes it into the deployment containers.

``sqrbot-jr-config.yaml``
   This is a ``ConfigMap`` called ``sqrbot-jr`` that defines environment variables that get injected into the app container.

``sqrbot-jr-deployment.yaml``
   This is a ``Deployment`` called ``sqrbot-jr`` that defines the actual application pods.

``sqrbot-jr-ingress.yaml``
   This is an ``Ingress`` called ``sqrbot-jr`` that defines an nginx-ingress-compatible ingress resources that
   routes external traffic on the app's URL path to the service.
