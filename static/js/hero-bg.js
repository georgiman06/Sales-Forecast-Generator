// Canvas setup
const canvas = document.getElementById('bg');
const ctx = canvas.getContext('2d', { alpha: true });

function resize() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}
resize();
window.addEventListener('resize', resize);

// Particle field
const DOTS = 90;            // total particles
const MAX_R = 3.2;          // max radius
const linksDist = 140;      // link distance
const dots = [];
const mouse = { x: null, y: null };

for (let i = 0; i < DOTS; i++) {
  dots.push({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    vx: (Math.random() - 0.5) * 0.6,
    vy: (Math.random() - 0.5) * 0.6,
    r: Math.random() * MAX_R + 0.6,
    hue: 195 + Math.random() * 40 // cyan/blue range
  });
}

window.addEventListener('mousemove', (e) => {
  mouse.x = e.clientX; mouse.y = e.clientY;
});
window.addEventListener('mouseleave', () => {
  mouse.x = null; mouse.y = null;
});

// Anime.js timeline to gently pulse speeds
anime({
  targets: dots,
  r: (el) => el.r * (1.05 + Math.random() * 0.2),
  duration: 2000,
  direction: 'alternate',
  easing: 'easeInOutSine',
  loop: true,
  delay: anime.stagger(12)
});

// Render loop
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // faint vignette
  const grad = ctx.createRadialGradient(
    canvas.width*0.5, canvas.height*0.5, 0,
    canvas.width*0.5, canvas.height*0.5, Math.max(canvas.width, canvas.height) * 0.8
  );
  grad.addColorStop(0, 'rgba(0,0,0,0)');
  grad.addColorStop(1, 'rgba(0,0,0,0.35)');
  ctx.fillStyle = grad;
  ctx.fillRect(0,0,canvas.width,canvas.height);

  // update + draw dots
  dots.forEach(p => {
    // slight attraction to mouse
    if (mouse.x !== null) {
      const dx = mouse.x - p.x, dy = mouse.y - p.y;
      const d = Math.hypot(dx, dy);
      if (d < 180) {
        p.vx += (dx / d) * 0.02;
        p.vy += (dy / d) * 0.02;
      }
    }

    p.x += p.vx; p.y += p.vy;

    // wrap around edges
    if (p.x < -10) p.x = canvas.width + 10;
    if (p.x > canvas.width + 10) p.x = -10;
    if (p.y < -10) p.y = canvas.height + 10;
    if (p.y > canvas.height + 10) p.y = -10;

    // glow dot
    ctx.beginPath();
    const color = `hsla(${p.hue}, 90%, 60%, 0.9)`;
    const glow = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r*4);
    glow.addColorStop(0, color);
    glow.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = glow;
    ctx.arc(p.x, p.y, p.r*4, 0, Math.PI*2);
    ctx.fill();

    ctx.beginPath();
    ctx.fillStyle = `hsla(${p.hue}, 90%, 70%, 0.95)`;
    ctx.arc(p.x, p.y, p.r, 0, Math.PI*2);
    ctx.fill();
  });

  // link close dots with faint lines
  ctx.lineWidth = 1;
  for (let i = 0; i < dots.length; i++) {
    for (let j = i + 1; j < dots.length; j++) {
      const a = dots[i], b = dots[j];
      const dx = a.x - b.x, dy = a.y - b.y;
      const d = Math.hypot(dx, dy);
      if (d < linksDist) {
        const alpha = 1 - d / linksDist;
        ctx.strokeStyle = `rgba(0, 198, 255, ${alpha * 0.25})`;
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.stroke();
      }
    }
  }

  requestAnimationFrame(draw);
}
draw();
