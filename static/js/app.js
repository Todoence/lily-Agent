document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("crawl-form");
  
    // Get DOM elements for each step
    const step1 = document.getElementById("step1");
    const step1Status = document.getElementById("step1-status");
    const step2 = document.getElementById("step2");
    const step2Status = document.getElementById("step2-status");
    const step3 = document.getElementById("step3");
    const step3Status = document.getElementById("step3-status");
    const step4 = document.getElementById("step4");
    const step4Status = document.getElementById("step4-status");
    const step5 = document.getElementById("step5");
    const step5Status = document.getElementById("step5-status");
  
    // Preview modal elements
    const previewModal = document.getElementById("preview-modal");
    const previewContent = document.getElementById("preview-content");
    const previewClose = document.getElementById("preview-close");
  
    // Global overlay
    const globalOverlay = document.getElementById("global-overlay");
  
    // Close modal event
    if (previewClose) {
      previewClose.addEventListener("click", function () {
        previewModal.style.display = "none";
      });
    }
  
    form.addEventListener("submit", function (event) {
      event.preventDefault();
  
      const rootUrl = document.getElementById("target_url").value;
  
      // --- Reset all steps ---
      step1.style.display = "flex";
      step1Status.className = "spinner";
      step1Status.textContent = "";
  
      step2.style.display = "none";
      step2Status.textContent = "";
      step3.style.display = "none";
      step3Status.textContent = "";
      step4.style.display = "none";
      step4Status.textContent = "";
      step5.style.display = "none";
      step5Status.textContent = "";
  
      // Remove old View buttons
      const oldViewBtns = document.querySelectorAll("[id^='view-btn']");
      oldViewBtns.forEach(btn => btn.remove());
  
      // --- Step 1: Call /generate_knowledge_base ---
      const requestData1 = { target_url: rootUrl, file_name: "knowledge_base" };
      fetch("/generate_knowledge_base", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestData1)
      })
        .then(response => {
          if (!response.ok) throw new Error(`Step 1 server error: ${response.status}`);
          return response.json();
        })
        .then(data1 => {
          console.log("Step 1 success:", data1);
          step1Status.className = "checkmark";
          step1Status.textContent = "✓";
  
          setTimeout(() => {
            // --- Step 2: Call /process_knowledge_base ---
            step2.style.display = "flex";
            step2Status.className = "spinner";
            step2Status.textContent = "";
            const requestData2 = { file_path: data1.file_path };
  
            fetch("/process_knowledge_base", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(requestData2)
            })
              .then(response => {
                if (!response.ok) throw new Error(`Step 2 server error: ${response.status}`);
                return response.json();
              })
              .then(data2 => {
                console.log("Step 2 success:", data2);
                step2Status.className = "checkmark";
                step2Status.textContent = "✓";
  
                // Add View button to preview company_profile.md
                const viewBtnStep2 = document.createElement("button");
                viewBtnStep2.textContent = "View";
                viewBtnStep2.id = "view-btn-step2";
                viewBtnStep2.style.marginLeft = "10px";
                viewBtnStep2.addEventListener("click", function () {
                  fetch("/view_company_profile")
                    .then(response => {
                      if (!response.ok) throw new Error(`Preview company profile server error: ${response.status}`);
                      return response.json();
                    })
                    .then(data => {
                      previewContent.innerHTML = `<div class="email-preview">${data.content}</div>`;
                      previewModal.style.display = "block";
                    })
                    .catch(err => {
                      console.error(err);
                      alert("Preview failed. Please check the console.");
                    });
                });
                step2.appendChild(viewBtnStep2);
  
                setTimeout(() => {
                  // --- Step 3: Call /find_potential_events ---
                  step3.style.display = "flex";
                  step3Status.className = "spinner";
                  step3Status.textContent = "";
                  const requestData3 = { file_path: "data/company_profile/company_profile.md" };
  
                  fetch("/find_potential_events", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(requestData3)
                  })
                    .then(response => {
                      if (!response.ok) throw new Error(`Step 3 server error: ${response.status}`);
                      return response.json();
                    })
                    .then(data3 => {
                      console.log("Step 3 success:", data3);
                      step3Status.className = "checkmark";
                      step3Status.textContent = "✓";
  
                      // Add View button to preview potential_events.json
                      const viewBtnStep3 = document.createElement("button");
                      viewBtnStep3.textContent = "View";
                      viewBtnStep3.id = "view-btn-step3";
                      viewBtnStep3.style.marginLeft = "10px";
                      viewBtnStep3.addEventListener("click", function () {
                        fetch("/view_potential_events")
                          .then(response => {
                            if (!response.ok) throw new Error(`Preview potential events server error: ${response.status}`);
                            return response.json();
                          })
                          .then(data => {
                            previewContent.innerHTML = `<div class="email-preview">${data.content}</div>`;
                            previewModal.style.display = "block";
                          })
                          .catch(err => {
                            console.error(err);
                            alert("Preview failed. Please check the console.");
                          });
                      });
                      step3.appendChild(viewBtnStep3);
  
                      setTimeout(() => {
                        // --- Step 4: Call /extract_companies ---
                        step4.style.display = "flex";
                        step4Status.className = "spinner";
                        step4Status.textContent = "";
                        const requestData4 = { json_file_path: "data/potential_events/potential_events.json" };
  
                        fetch("/extract_companies", {
                          method: "POST",
                          headers: { "Content-Type": "application/json" },
                          body: JSON.stringify(requestData4)
                        })
                          .then(response => {
                            if (!response.ok) throw new Error(`Step 4 server error: ${response.status}`);
                            return response.json();
                          })
                          .then(data4 => {
                            console.log("Step 4 success:", data4);
                            step4Status.className = "checkmark";
                            step4Status.textContent = "✓";
  
                            // Add View button to preview potential_customer.json
                            const viewBtnStep4 = document.createElement("button");
                            viewBtnStep4.textContent = "View";
                            viewBtnStep4.id = "view-btn-step4";
                            viewBtnStep4.style.marginLeft = "10px";
                            viewBtnStep4.addEventListener("click", function () {
                              fetch("/view_potential_customer")
                                .then(response => {
                                  if (!response.ok) throw new Error(`Preview potential customer server error: ${response.status}`);
                                  return response.json();
                                })
                                .then(data => {
                                  previewContent.innerHTML = `<div class="email-preview">${data.content}</div>`;
                                  previewModal.style.display = "block";
                                })
                                .catch(err => {
                                  console.error(err);
                                  alert("Preview failed. Please check the console.");
                                });
                            });
                            step4.appendChild(viewBtnStep4);
  
                            setTimeout(() => {
                              // --- Step 5: Call /prioritize_companies ---
                              step5.style.display = "flex";
                              step5Status.className = "spinner";
                              step5Status.textContent = "";
                              const requestData5 = {
                                potential_customer_path: "data/potential_customer/potential_customer.json",
                                company_profile_path: "data/company_profile/company_profile.md"
                              };
  
                              fetch("/prioritize_companies", {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify(requestData5)
                              })
                                .then(response => {
                                  if (!response.ok) throw new Error(`Step 5 server error: ${response.status}`);
                                  return response.json();
                                })
                                .then(data5 => {
                                  console.log("Step 5 success:", data5);
                                  step5Status.className = "checkmark";
                                  step5Status.textContent = "✓";
  
                                  // Add View button to preview prioritized_companies.json
                                  const viewBtnStep5 = document.createElement("button");
                                  viewBtnStep5.textContent = "View";
                                  viewBtnStep5.id = "view-btn-step5";
                                  viewBtnStep5.style.marginLeft = "10px";
                                  viewBtnStep5.addEventListener("click", function () {
                                    fetch("/view_prioritized_companies")
                                      .then(response => {
                                        if (!response.ok) throw new Error(`Preview prioritized companies server error: ${response.status}`);
                                        return response.json();
                                      })
                                      .then(data => {
                                        let companies = [];
                                        try {
                                          companies = JSON.parse(data.content);
                                        } catch (e) {
                                          console.error("Failed to parse JSON:", e);
                                        }
                                        previewContent.innerHTML = "";
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
                                            const outreachBtn = document.createElement("button");
                                            outreachBtn.textContent = "Outreach";
                                            outreachBtn.className = "outreach-btn";
                                            outreachBtn.addEventListener("click", function () {
                                              // Show global overlay to prevent duplicate clicks
                                              globalOverlay.style.display = "flex";
  
                                              // Add spinner after the button
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
                                                  previewContent.innerHTML = `<h3>Outreach Email Preview</h3><div class="email-preview">${emailData.email}</div>`;
                                                  previewModal.style.display = "block";
                                                })
                                                .catch(err => {
                                                  btnSpinner.remove();
                                                  globalOverlay.style.display = "none";
                                                  console.error("Failed to generate email:", err);
                                                  alert("Email generation failed.");
                                                });
                                            });
                                            card.appendChild(outreachBtn);
                                            previewContent.appendChild(card);
                                          });
                                        } else {
                                          previewContent.textContent = "No company data found.";
                                        }
                                        previewModal.style.display = "block";
                                      })
                                      .catch(err => {
                                        console.error(err);
                                        alert("Preview failed. Please check the console.");
                                      });
                                  });
                                  step5.appendChild(viewBtnStep5);
  
                                  // Add Dashboard button under step 5
                                  const dashboardBtn = document.createElement("button");
                                  dashboardBtn.textContent = "Dashboard";
                                  dashboardBtn.style.marginLeft = "10px";
                                  dashboardBtn.addEventListener("click", function () {
                                    window.location.href = "/dashboard";
                                  });
                                  step5.appendChild(dashboardBtn);
                                })
                                .catch(error => {
                                  console.error("Step 5 request failed:", error);
                                  step5Status.className = "";
                                  step5Status.textContent = "×";
                                  step5Status.style.color = "red";
                                });
                            }, 1000);
                          })
                          .catch(error => {
                            console.error("Step 4 request failed:", error);
                            step4Status.className = "";
                            step4Status.textContent = "×";
                            step4Status.style.color = "red";
                          });
                      }, 1000);
                    })
                    .catch(error => {
                      console.error("Step 3 request failed:", error);
                      step3Status.className = "";
                      step3Status.textContent = "×";
                      step3Status.style.color = "red";
                    });
                }, 1000);
              })
              .catch(error => {
                console.error("Step 2 request failed:", error);
                step2Status.className = "";
                step2Status.textContent = "×";
                step2Status.style.color = "red";
              });
          }, 1000);
        })
        .catch(error => {
          console.error("Step 1 request failed:", error);
          step1Status.className = "";
          step1Status.textContent = "×";
          step1Status.style.color = "red";
        });
    });
  });
  