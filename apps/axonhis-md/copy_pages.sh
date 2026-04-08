#!/bin/bash
# Create all module page directories
for dir in organizations clinicians patients appointments encounters specialties orders devices documents sharing channels coverage billing prescriptions integration audit; do
  mkdir -p /home/sujeetnew/Downloads/AXONHIS/apps/axonhis-md/src/app/dashboard/${dir}
done
echo "Directories created"
