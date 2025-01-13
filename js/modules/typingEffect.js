class TypingEffect {
    constructor(element, phrases, options = {}) {
        this.element = element;
        this.phrases = phrases;
        this.currentPhrase = 0;
        this.currentChar = 0;
        this.isDeleting = false;
        this.options = {
        typeSpeed: options.typeSpeed || 100,
        deleteSpeed: options.deleteSpeed || 50,
        pauseTime: options.pauseTime || 2000
        };
    }

    type() {
        const phrase = this.phrases[this.currentPhrase];
        
        if (this.isDeleting) {
        this.element.textContent = phrase.substring(0, this.currentChar - 1);
        this.currentChar--;
        } else {
        this.element.textContent = phrase.substring(0, this.currentChar + 1);
        this.currentChar++;
        }

        let typeSpeed = this.isDeleting ? this.options.deleteSpeed : this.options.typeSpeed;

        if (!this.isDeleting && this.currentChar === phrase.length) {
        typeSpeed = this.options.pauseTime;
        this.isDeleting = true;
        } else if (this.isDeleting && this.currentChar === 0) {
        this.isDeleting = false;
        this.currentPhrase = (this.currentPhrase + 1) % this.phrases.length;
        typeSpeed = 500;
        }

        setTimeout(() => this.type(), typeSpeed);
    }
}

    // Initialize the typing effect
    const typingElement = document.querySelector('.typing-text');
    const phrases = [
        'Hello, welcome to my portfolio!',
        'I love coding',
        'Check out my work below'
    ];

    const typing = new TypingEffect(typingElement, phrases);
    typing.type();