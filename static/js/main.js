/**
 * BallotBridge — Secure E-Voting Platform
 * Interactive Client Utilities
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Navigation Drawer Toggle
  const mobileToggle = document.getElementById('mobileNavToggle');
  const mobileNavMenu = document.getElementById('mobileNavMenu');
  if (mobileToggle && mobileNavMenu) {
    mobileToggle.addEventListener('click', () => {
      mobileNavMenu.classList.toggle('is-open');
    });
  }

  // 2. Alert Dismissal
  const alertCloseBtns = document.querySelectorAll('.alert-close');
  alertCloseBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      const alert = e.target.closest('.alert');
      if (alert) {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-10px)';
        setTimeout(() => alert.remove(), 250);
      }
    });
  });

  // 3. Interactive Candidate Selection in Voting Step
  const candidateCards = document.querySelectorAll('.selectable-candidate-card');
  const hiddenCandidateInput = document.getElementById('selectedCandidateId');
  const proceedVoteBtn = document.getElementById('proceedVoteBtn');

  candidateCards.forEach(card => {
    card.addEventListener('click', () => {
      // Remove selected from others
      candidateCards.forEach(c => c.classList.remove('selected'));
      // Add to this
      card.classList.add('selected');
      const candidateId = card.getAttribute('data-candidate-id');
      if (hiddenCandidateInput) {
        hiddenCandidateInput.value = candidateId;
      }
      if (proceedVoteBtn) {
        proceedVoteBtn.removeAttribute('disabled');
      }
    });
  });

  // 4. Copy Receipt Token to Clipboard
  window.copyReceiptToken = function(tokenId) {
    const el = document.getElementById(tokenId);
    if (!el) return;
    const text = el.innerText || el.textContent;
    navigator.clipboard.writeText(text.trim()).then(() => {
      const copyBtn = document.getElementById('copyBtnText');
      if (copyBtn) {
        const originalText = copyBtn.innerText;
        copyBtn.innerText = 'Copied to Clipboard!';
        setTimeout(() => {
          copyBtn.innerText = originalText;
        }, 2000);
      }
    }).catch(err => {
      console.error('Could not copy text: ', err);
    });
  };

  // 5. Filter Dashboard Tabs
  window.switchTab = function(tabName) {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');

    tabBtns.forEach(b => b.classList.remove('active'));
    tabPanes.forEach(p => p.classList.remove('active'));

    const activeBtn = document.querySelector(`[data-tab-target="${tabName}"]`);
    const activePane = document.getElementById(`tab-${tabName}`);

    if (activeBtn) activeBtn.classList.add('active');
    if (activePane) activePane.classList.add('active');
  };

  // 6. Accordion toggle for FAQ
  const faqItems = document.querySelectorAll('.faq-item-header');
  faqItems.forEach(header => {
    header.addEventListener('click', () => {
      const item = header.parentElement;
      item.classList.toggle('active');
      const icon = header.querySelector('.faq-icon');
      if (icon) {
        icon.classList.toggle('rotated');
      }
    });
  });
});
