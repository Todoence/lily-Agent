document.addEventListener("DOMContentLoaded", function () {
    // Get column containers
    const eventsList = document.getElementById("events-list");
    const customersList = document.getElementById("customers-list");
    const prioritizedList = document.getElementById("prioritized-list");
    const backButton = document.getElementById("back-button");
  
    // Get preview modal elements
    const previewModal = document.getElementById("preview-modal");
    const previewContent = document.getElementById("preview-content");
    const previewClose = document.getElementById("preview-close");
  
    // Global overlay (used to block UI during Outlook requests)
    const globalOverlay = document.getElementById("global-overlay");
  
    // Close preview modal
    if (previewClose) {
      previewClose.addEventListener("click", function () {
        previewModal.style.display = "none";
      });
    }
  
    // Back button click event
    backButton.addEventListener("click", function () {
      window.location.href = "/";
    });
  
    // Helper function: fetch data from API and call callback to process it
    function loadData(url, callback) {
      fetch(url)
        .then(response => {
          if (!response.ok) throw new Error(`Error: ${response.status}`);
          return response.json();
        })
        .then(data => callback(data))
        .catch(err => console.error(`Failed to load ${url}:`, err));
    }
  
    // Load potential events data
    loadData("/view_potential_events", function (data) {
      let events = [];
      try {
        events = JSON.parse(data.content);
      } catch (e) {
        console.error("Failed to parse potential events JSON:", e);
      }
      eventsList.innerHTML = "";
      if (Array.isArray(events) && events.length > 0) {
        events.forEach(event => {
          const card = document.createElement("div");
          card.className = "card";
          card.innerHTML = `
            <h3>${event.name}</h3>
            <p><strong>URL:</strong> <a href="${event.url}" target="_blank">${event.url}</a></p>
            <p><strong>Category:</strong> ${event.category}</p>
          `;
          eventsList.appendChild(card);
        });
      } else {
        eventsList.textContent = "No potential events available.";
      }
    });
  
    // Load potential customers data
    loadData("/view_potential_customer", function (data) {
      let companies = [];
      try {
        // Assume response format is { success: true, data: { companies: [ ... ] } }
        const parsed = JSON.parse(data.content);
        companies = parsed.data.companies || [];
      } catch (e) {
        console.error("Failed to parse potential customers JSON:", e);
      }
      customersList.innerHTML = "";
      if (companies.length > 0) {
        const ul = document.createElement("ul");
        ul.className = "company-list";
        companies.forEach(company => {
          const li = document.createElement("li");
          li.textContent = company;
          ul.appendChild(li);
        });
        customersList.appendChild(ul);
      } else {
        customersList.textContent = "No potential customers available.";
      }
    });
  
    // Load prioritized companies data
    loadData("/view_prioritized_companies", function (data) {
      let companies = [];
      try {
        companies = JSON.parse(data.content);
      } catch (e) {
        console.error("Failed to parse prioritized companies JSON:", e);
      }
      prioritizedList.innerHTML = "";
      if (Array.isArray(companies) && companies.length > 0) {
        companies.forEach(company => {
          const card = document.createElement("div");
          card.className = "card";
          card.innerHTML = `
            <h3>${company.company_name}</h3>
            <p><strong>Industry:</strong> ${company.industry}</p>
            <p><strong>Revenue:</strong> ${company.revenue}</p>
            <p><strong>Size:</strong> ${company.size}</p>
            <p><strong>Stakeholder:</strong> ${company.stakeholder_name} - ${company.stakeholder_position}</p>
            <p><strong>Email:</strong> ${company.stakeholder_email}</p>
            <p><strong>Phone:</strong> ${company.stakeholder_phone}</p>
            <p><strong>LinkedIn:</strong> ${company.stakeholder_link}</p>
            <p><strong>Reasoning:</strong> ${company.reasoning}</p>
          `;
          // Add Outreach button (only shown on prioritized cards)
          const outreachBtn = document.createElement("button");
          outreachBtn.textContent = "Outreach";
          outreachBtn.className = "outreach-btn";
          outreachBtn.addEventListener("click", function () {
            // Show global overlay to prevent duplicate clicks
            globalOverlay.style.display = "flex";
            // Add a small spinner next to the button
            const btnSpinner = document.createElement("span");
            btnSpinner.className = "spinner";
            btnSpinner.style.marginLeft = "10px";
            outreachBtn.parentNode.insertBefore(btnSpinner, outreachBtn.nextSibling);
  
            fetch("/generate_outreach_email", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(company)
            })
              .then(response => {
                if (!response.ok) throw new Error(`Error: ${response.status}`);
                return response.json();
              })
              .then(emailData => {
                btnSpinner.remove();
                globalOverlay.style.display = "none";
                // Show email preview with formatted layout
                previewContent.innerHTML = `<h3>Outreach Email Preview</h3><div class="email-preview">${emailData.email}</div>`;
                previewModal.style.display = "block";
              })
              .catch(err => {
                btnSpinner.remove();
                globalOverlay.style.display = "none";
                console.error("Failed to generate outreach email:", err);
                alert("Failed to generate outreach email.");
              });
          });
          card.appendChild(outreachBtn);
          prioritizedList.appendChild(card);
        });
      } else {
        prioritizedList.textContent = "No prioritized companies available.";
      }
    });
  });
  