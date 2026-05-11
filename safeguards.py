js_page_switch = """
<script>
    {
        function showCustomWarning() {
            // Create overlay
            const overlay = document.createElement('div');
            overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.6);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 10000;
            `;

            // Create modal box
            const modal = document.createElement('div');
            modal.style.cssText = `
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
                max-width: 500px;
                text-align: center;
                z-index: 10001;
            `;

            modal.innerHTML = `
                <h2 style="color: #d32f2f; margin-bottom: 15px;">⚠️ Warning</h2>
                <p style="font-size: 16px; color: #333; line-height: 1.6;">
                    Please do not leave this page. To ensure fair play and prevent the use of AI tools during the game, navigating away may result in the session being ended early.
                </p>
                <button id="dismissBtn" style="
                    margin-top: 20px;
                    padding: 10px 30px;
                    background-color: #d32f2f;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-size: 16px;
                    cursor: pointer;
                ">I Understand</button>
            `;

            overlay.appendChild(modal);
            document.body.appendChild(overlay);

            // Close when button clicked
            document.getElementById('dismissBtn').addEventListener('click', function() {
                overlay.remove();
            });
        }

        window.addEventListener("blur", function() {
            showCustomWarning();
        });
    }
</script>
"""