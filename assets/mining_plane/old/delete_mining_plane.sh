#! /bin/bash
helm uninstall -n mining-plane scdf
helm uninstall -n mining-plane hue
kubectl delete pvc -n mining-plane --all
