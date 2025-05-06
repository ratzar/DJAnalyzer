cat > src/main.py << 'EOF'
from djprotool import DJProToolApp

if __name__ == "__main__":
    app = DJProToolApp()
    app.mainloop()
EOF
