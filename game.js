const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

// --- Audio System ---
const AudioContext = window.AudioContext || window.webkitAudioContext;
let audioCtx;
try {
    audioCtx = new AudioContext();
} catch (e) {
    console.warn("Web Audio API not supported");
}

function playSound(type) {
    if (!audioCtx) return;
    if (audioCtx.state === 'suspended') audioCtx.resume();
    
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    
    if (type === 'hit') {
        osc.type = 'square';
        osc.frequency.setValueAtTime(440, audioCtx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(880, audioCtx.currentTime + 0.1);
        gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.1);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.1);
    } else if (type === 'score') {
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(220, audioCtx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(110, audioCtx.currentTime + 0.3);
        gain.gain.setValueAtTime(0.15, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.3);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.3);
    } else if (type === 'wall') {
        osc.type = 'sine';
        osc.frequency.setValueAtTime(200, audioCtx.currentTime);
        gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.1);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.1);
    }
}

// Game Settings
let mode = 'bot'; // 'bot' or 'pvp'
let difficulty = 'medium';
let speedMultiplier = 1;
let screenShake = 0;

let WIN_SCORE = 10;
let gameOver = false;
let winnerText = "";
const maxBallSpeed = 25;

const themes = {
    green: { fg: '#0fa', bg: '#02110c', fgRgb: '0, 255, 170' },
    magenta: { fg: '#f0f', bg: '#100110', fgRgb: '255, 0, 255' },
    cyan: { fg: '#0ff', bg: '#001111', fgRgb: '0, 255, 255' },
    white: { fg: '#fff', bg: '#111111', fgRgb: '255, 255, 255' }
};
let currentTheme = themes.green;

const botSpeeds = {
    easy: 0.6, medium: 0.9, hard: 1.2, insane: 1.6, extreme: 2.0
};

// Particles & Trails
let particles = [];
let trail = [];

const ball = { x: canvas.width / 2, y: canvas.height / 2, size: 10, speedX: 5, speedY: 5, baseSpeed: 5 };
// Player movement tuning for smoothness
const paddle = { width: 10, height: 80, accel: 3, friction: 0.8, maxSpeed: 18 };
const p1 = { x: 20, y: canvas.height / 2 - paddle.height / 2, vy: 0, score: 0, name: 'PLAYER 1' };
const p2 = { x: canvas.width - 30, y: canvas.height / 2 - paddle.height / 2, vy: 0, score: 0, name: 'PLAYER 2' };

const keys = { w: false, s: false, ArrowUp: false, ArrowDown: false };
window.addEventListener('keydown', e => { if(keys.hasOwnProperty(e.key)) keys[e.key] = true; });
window.addEventListener('keyup', e => { if(keys.hasOwnProperty(e.key)) keys[e.key] = false; });

// --- UI Navigation & Screen State ---
const screens = document.querySelectorAll('.screen');
function showScreen(id) {
    screens.forEach(s => s.classList.remove('active'));
    document.getElementById(id).classList.add('active');
}

function startNewGame(selectedMode) {
    mode = selectedMode;
    p1.name = document.getElementById('p1Name').value.trim().toUpperCase() || 'PLAYER 1';
    
    if (selectedMode === 'bot') {
        p2.name = 'BOT ' + difficulty.toUpperCase();
    } else {
        p2.name = document.getElementById('p2Name').value.trim().toUpperCase() || 'PLAYER 2';
    }

    p1.score = 0; 
    p2.score = 0;
    p1.vy = 0;
    p2.vy = 0;
    gameOver = false;
    resetBall();
    showScreen('game-screen');
    if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume();
}

document.getElementById('btn-vs-ai').addEventListener('click', () => startNewGame('bot'));
document.getElementById('btn-vs-player').addEventListener('click', () => startNewGame('pvp'));

document.getElementById('btn-settings').addEventListener('click', () => {
    showScreen('settings-menu');
});

document.getElementById('btn-back').addEventListener('click', () => {
    showScreen('main-menu');
});

document.getElementById('restartBtn').addEventListener('click', () => {
    gameOver = true;
    showScreen('main-menu');
});

// Settings Elements mapping
document.getElementById('botDifficulty').addEventListener('change', e => difficulty = e.target.value);
document.getElementById('gameSpeed').addEventListener('change', e => {
    speedMultiplier = parseFloat(e.target.value);
    resetBall(); 
});
document.getElementById('gameWinScore').addEventListener('change', e => {
    let val = parseInt(e.target.value);
    if (isNaN(val) || val < 3) val = 3;
    if (val > 10) val = 10;
    e.target.value = val;
    WIN_SCORE = val;
});
document.getElementById('gameTheme').addEventListener('change', e => {
    currentTheme = themes[e.target.value] || themes.green;
    document.documentElement.style.setProperty('--neon-green', currentTheme.fg);
    document.documentElement.style.setProperty('--neon-bg', currentTheme.bg);
});

function createParticles(x, y, isWall) {
    let count = isWall ? 5 : 15;
    for (let i = 0; i < count; i++) {
        particles.push({
            x: x,
            y: y,
            vx: (Math.random() - 0.5) * 10,
            vy: (Math.random() - 0.5) * 10,
            life: 1,
            size: Math.random() * 4 + 2
        });
    }
}

function updateParticles() {
    for (let i = particles.length - 1; i >= 0; i--) {
        let p = particles[i];
        p.x += p.vx;
        p.y += p.vy;
        p.life -= 0.03;
        if (p.life <= 0) particles.splice(i, 1);
    }
}

function resetBall() {
    ball.x = canvas.width / 2;
    ball.y = canvas.height / 2;
    let dirX = Math.random() > 0.5 ? 1 : -1;
    let dirY = Math.random() > 0.5 ? 1 : -1;
    ball.speedX = ball.baseSpeed * speedMultiplier * dirX;
    ball.speedY = ball.baseSpeed * speedMultiplier * dirY;
    trail = [];
    playSound('score');
}

function checkWin() {
    if (p1.score >= WIN_SCORE) {
        gameOver = true;
        winnerText = "PLAYER 1 WINS!";
        setTimeout(() => showScreen('main-menu'), 3000);
    } else if (p2.score >= WIN_SCORE) {
        gameOver = true;
        winnerText = mode === 'bot' ? "BOT WINS!" : "PLAYER 2 WINS!";
        setTimeout(() => showScreen('main-menu'), 3000);
    }
}

function update() {
    if (gameOver) return;

    // Smoothed Player 1 Movement
    let frameAccel = paddle.accel * speedMultiplier;
    let frameMaxSpeed = paddle.maxSpeed * speedMultiplier;
    
    if (keys.w) p1.vy -= frameAccel;
    if (keys.s) p1.vy += frameAccel;
    p1.vy *= paddle.friction;
    
    // Clamp speed
    if (p1.vy > frameMaxSpeed) p1.vy = frameMaxSpeed;
    if (p1.vy < -frameMaxSpeed) p1.vy = -frameMaxSpeed;

    p1.y += p1.vy;
    if (p1.y < 0) { p1.y = 0; p1.vy = 0; }
    if (p1.y > canvas.height - paddle.height) { p1.y = canvas.height - paddle.height; p1.vy = 0; }

    // Smoothed Player 2 / Bot Movement
    if (mode === 'pvp') {
        if (keys.ArrowUp) p2.vy -= frameAccel;
        if (keys.ArrowDown) p2.vy += frameAccel;
        p2.vy *= paddle.friction;

        if (p2.vy > frameMaxSpeed) p2.vy = frameMaxSpeed;
        if (p2.vy < -frameMaxSpeed) p2.vy = -frameMaxSpeed;

        p2.y += p2.vy;
        if (p2.y < 0) { p2.y = 0; p2.vy = 0; }
        if (p2.y > canvas.height - paddle.height) { p2.y = canvas.height - paddle.height; p2.vy = 0; }
    } else {
        let botMaxSpeed = botSpeeds[difficulty] * speedMultiplier;
        let targetY = ball.y - paddle.height / 2;

        if ((difficulty === 'insane' || difficulty === 'extreme') && ball.speedX > 0) {
            let timeToReach = (p2.x - ball.x) / ball.speedX;
            targetY = ball.y + (ball.speedY * timeToReach) - paddle.height / 2;
            let tempY = targetY;
            let bounces = 0;
            while ((tempY < 0 || tempY > canvas.height - paddle.height) && bounces < 5) {
                if (tempY < 0) tempY = Math.abs(tempY);
                if (tempY > canvas.height - paddle.height) tempY = 2 * (canvas.height - paddle.height) - tempY;
                bounces++;
            }
            targetY = tempY;
        } else if (ball.speedX < 0 && difficulty !== 'extreme') {
             targetY = canvas.height / 2 - paddle.height / 2;
        } else if (difficulty !== 'insane' && difficulty !== 'extreme') {
             // Delay reaction for easy, medium, hard bots (makes them dumber and late)
             let reactionThresholds = { easy: 0.65, medium: 0.45, hard: 0.15 };
             if (ball.x / canvas.width > reactionThresholds[difficulty]) {
                 targetY = ball.y - paddle.height / 2; // Start tracking
             } else {
                 targetY = canvas.height / 2 - paddle.height / 2; // Lazy return to center
             }
        }

        if (p2.y < targetY - botMaxSpeed) { p2.y += botMaxSpeed; p2.vy = botMaxSpeed; }
        else if (p2.y > targetY + botMaxSpeed) { p2.y -= botMaxSpeed; p2.vy = -botMaxSpeed; }
        else { p2.y = targetY; p2.vy = 0; }
        
        p2.y = Math.max(0, Math.min(canvas.height - paddle.height, p2.y));
    }

    // Ball Movement & Trail update
    trail.push({x: ball.x, y: ball.y});
    if (trail.length > 10) trail.shift();

    ball.x += ball.speedX;
    ball.y += ball.speedY;

    // Wall Collision (Top/Bottom)
    if (ball.y <= 0 || ball.y + ball.size >= canvas.height) {
        ball.speedY *= -1.05; // Escalating speed on wall bounce
        ball.speedX *= 1.05;
        
        let speed = Math.sqrt(ball.speedX*ball.speedX + ball.speedY*ball.speedY);
        if (speed > maxBallSpeed) {
            ball.speedX = (ball.speedX / speed) * maxBallSpeed;
            ball.speedY = (ball.speedY / speed) * maxBallSpeed;
        }

        createParticles(ball.x, ball.y, true);
        playSound('wall');
        screenShake = 3;
    }

    const MAX_BOUNCE_ANGLE = Math.PI / 3; // 60 degrees
    
    // Paddle Collision - P1 Hit
    if (ball.x <= p1.x + paddle.width && ball.y + ball.size >= p1.y && ball.y <= p1.y + paddle.height && ball.speedX < 0) {
        ball.speedX *= -1.08; 
        let intersectY = (ball.y + ball.size / 2) - (p1.y + paddle.height / 2);
        let normalizedIntersect = intersectY / (paddle.height / 2);
        let bounceAngle = normalizedIntersect * MAX_BOUNCE_ANGLE;
        
        // Add spin/friction based on paddle smooth velocity
        bounceAngle += (p1.vy * 0.02);

        let speed = Math.sqrt(ball.speedX*ball.speedX + ball.speedY*ball.speedY);
        ball.speedX = speed * Math.cos(bounceAngle);
        ball.speedY = speed * Math.sin(bounceAngle);
        
        createParticles(ball.x, ball.y, false);
        playSound('hit');
        screenShake = 5;
    }
    
    // Paddle Collision - P2 Hit
    if (ball.x + ball.size >= p2.x && ball.y + ball.size >= p2.y && ball.y <= p2.y + paddle.height && ball.speedX > 0) {
        ball.speedX *= -1.08; 
        let intersectY = (ball.y + ball.size / 2) - (p2.y + paddle.height / 2);
        let normalizedIntersect = intersectY / (paddle.height / 2);
        let bounceAngle = normalizedIntersect * MAX_BOUNCE_ANGLE;
        
        bounceAngle += (p2.vy * 0.02);

        let speed = Math.sqrt(ball.speedX*ball.speedX + ball.speedY*ball.speedY);
        ball.speedX = -Math.abs(speed * Math.cos(bounceAngle));
        ball.speedY = speed * Math.sin(bounceAngle);
        
        createParticles(ball.x, ball.y, false);
        playSound('hit');
        screenShake = 5;
    }

    // Scoring
    if (ball.x < -20) { p2.score++; screenShake = 15; checkWin(); if (!gameOver) resetBall(); }
    if (ball.x > canvas.width + 20) { p1.score++; screenShake = 15; checkWin(); if (!gameOver) resetBall(); }

    updateParticles();
    if (screenShake > 0) screenShake *= 0.9;
    if (screenShake < 0.5) screenShake = 0;
}

function draw() {
    ctx.save();
    
    // Screen Shake application
    if (screenShake > 0) {
        let dx = (Math.random() - 0.5) * screenShake;
        let dy = (Math.random() - 0.5) * screenShake;
        ctx.translate(dx, dy);
    }
    
    // Clear with slight trailing alpha for motion blur
    ctx.fillStyle = `rgba(0, 0, 0, 0.4)`;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const neonGreen = currentTheme.fg;
    const fgRgb = currentTheme.fgRgb;

    // Center Line
    ctx.fillStyle = `rgba(${fgRgb}, 0.2)`;
    for(let i = 0; i < canvas.height; i += 30) {
        ctx.fillRect(canvas.width / 2 - 1, i, 2, 15);
    }

    // Ball Trail
    ctx.beginPath();
    if (trail.length > 0) {
        ctx.moveTo(trail[0].x + ball.size/2, trail[0].y + ball.size/2);
        for(let i = 1; i < trail.length; i++) {
            ctx.lineTo(trail[i].x + ball.size/2, trail[i].y + ball.size/2);
        }
    }
    ctx.strokeStyle = `rgba(${fgRgb}, 0.3)`;
    ctx.lineWidth = ball.size;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.stroke();

    // Draw Particles
    for (let p of particles) {
        ctx.fillStyle = `rgba(${fgRgb}, ${p.life})`;
        ctx.fillRect(p.x, p.y, p.size, p.size);
    }

    // Common styling for glowing elements
    ctx.shadowBlur = 10;
    ctx.shadowColor = neonGreen;
    ctx.fillStyle = neonGreen;

    // Draw Paddles & Ball
    ctx.fillRect(p1.x, p1.y, paddle.width, paddle.height);
    ctx.fillRect(p2.x, p2.y, paddle.width, paddle.height);
    
    ctx.shadowBlur = 20; 
    ctx.fillRect(ball.x, ball.y, ball.size, ball.size);

    // Draw Scores
    ctx.shadowBlur = 15;
    ctx.font = '40px "Press Start 2P"';
    ctx.textAlign = 'center';
    ctx.fillText(p1.score, canvas.width / 4, 75);
    ctx.fillText(p2.score, 3 * canvas.width / 4, 75);

    // Draw Names
    ctx.font = '12px "Press Start 2P"';
    ctx.fillText(p1.name, canvas.width / 4, 30);
    ctx.fillText(p2.name, 3 * canvas.width / 4, 30);

    // Draw Target Score
    ctx.font = '12px "Press Start 2P"';
    ctx.fillText(`TARGET: ${WIN_SCORE}`, canvas.width / 2, 30);
    ctx.textAlign = 'left';

    // Draw Victory Screen overlay
    if (gameOver) {
        ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        ctx.fillStyle = neonGreen;
        ctx.textAlign = 'center';
        ctx.shadowBlur = 30;
        
        ctx.font = '50px "Press Start 2P"';
        ctx.fillText(winnerText, canvas.width / 2, canvas.height / 2 - 20);
        
        ctx.font = '15px "Press Start 2P"';
        ctx.fillText("RETURNING TO MENU...", canvas.width / 2, canvas.height / 2 + 40);
        ctx.textAlign = 'left';
    }

    ctx.restore();
}

function gameLoop() {
    update();
    draw();
    requestAnimationFrame(gameLoop);
}

// Start Game
resetBall();
gameLoop();

// Listen to first user interaction to resume AudioContext (browser policy)
document.addEventListener('click', () => { if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume(); }, {once:true});
document.addEventListener('keydown', () => { if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume(); }, {once:true});