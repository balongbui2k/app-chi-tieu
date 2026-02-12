const tg = window.Telegram.WebApp;

// Initialize Telegram WebApp
tg.expand();

// Theme handling
document.documentElement.style.setProperty('--bg-color', tg.backgroundColor || '#ffffff');
document.documentElement.style.setProperty('--text-color', tg.textColor || '#000000');
document.documentElement.style.setProperty('--button-color', tg.buttonColor || '#3390ec');
document.documentElement.style.setProperty('--button-text-color', tg.buttonTextColor || '#ffffff');

// Valid categories
let currentCategory = 'Khác';

function selectCategory(cat) {
    currentCategory = cat;
    document.getElementById('category').value = cat;
    
    // Update UI
    document.querySelectorAll('.cat-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.innerText.includes(cat)) {
            btn.classList.add('active');
        }
    });
}

function addAmount(val) {
    const input = document.getElementById('amount');
    let current = parseInt(input.value.replace(/\D/g, '')) || 0;
    input.value = current + val;
}

function submitExpense() {
    const amount = document.getElementById('amount').value;
    const desc = document.getElementById('desc').value;
    const person = document.getElementById('person').value;
    
    if (!amount) {
        tg.showAlert("Vui lòng nhập số tiền!");
        return;
    }

    const data = {
        amount: parseInt(amount.replace(/\D/g, '')),
        category: currentCategory,
        description: desc || currentCategory, // Default desc to category if empty
        person: person
    };

    // Send data back to bot
    tg.sendData(JSON.stringify(data));
    
    // Close WebApp
    tg.close();
}

// Set default category
selectCategory('Ăn uống');
