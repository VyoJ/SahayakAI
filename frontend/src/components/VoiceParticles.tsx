import { useEffect, useRef } from 'react';

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  opacity: number;
  life: number;
  maxLife: number;
  color: string;
}

interface VoiceParticlesProps {
  isActive: boolean;
  intensity?: number;
}

const VoiceParticles = ({ isActive, intensity = 0.5 }: VoiceParticlesProps) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particlesRef = useRef<Particle[]>([]);
  const animationFrameRef = useRef<number>();

  const colors = [
    'rgba(147, 51, 234, 0.8)', // purple
    'rgba(79, 70, 229, 0.8)',  // indigo
    'rgba(59, 130, 246, 0.8)', // blue
    'rgba(168, 85, 247, 0.8)', // violet
    'rgba(236, 72, 153, 0.8)', // pink
  ];

  const createParticle = (canvas: HTMLCanvasElement): Particle => {
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const angle = Math.random() * Math.PI * 2;
    const distance = Math.random() * 100 + 50;
    
    return {
      x: centerX + Math.cos(angle) * distance,
      y: centerY + Math.sin(angle) * distance,
      vx: (Math.random() - 0.5) * 2,
      vy: (Math.random() - 0.5) * 2,
      size: Math.random() * 3 + 1,
      opacity: Math.random() * 0.8 + 0.2,
      life: 0,
      maxLife: Math.random() * 120 + 60,
      color: colors[Math.floor(Math.random() * colors.length)]
    };
  };

  const updateParticle = (particle: Particle, canvas: HTMLCanvasElement, deltaIntensity: number) => {
    particle.life += 1;
    particle.x += particle.vx * (1 + deltaIntensity);
    particle.y += particle.vy * (1 + deltaIntensity);
    
    // Fade out as particle ages
    particle.opacity = Math.max(0, 1 - (particle.life / particle.maxLife));
    
    // Apply some gravitational pull towards center when intensity is high
    if (intensity > 0.3) {
      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;
      const dx = centerX - particle.x;
      const dy = centerY - particle.y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      
      if (distance > 0) {
        particle.vx += (dx / distance) * 0.02 * intensity;
        particle.vy += (dy / distance) * 0.02 * intensity;
      }
    }
    
    // Bounce off edges
    if (particle.x < 0 || particle.x > canvas.width) particle.vx *= -0.8;
    if (particle.y < 0 || particle.y > canvas.height) particle.vy *= -0.8;
    
    // Keep particles in bounds
    particle.x = Math.max(0, Math.min(canvas.width, particle.x));
    particle.y = Math.max(0, Math.min(canvas.height, particle.y));
  };

  const drawParticle = (ctx: CanvasRenderingContext2D, particle: Particle) => {
    ctx.save();
    ctx.globalAlpha = particle.opacity;
    ctx.fillStyle = particle.color;
    ctx.shadowColor = particle.color;
    ctx.shadowBlur = 10;
    
    ctx.beginPath();
    ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
    ctx.fill();
    
    // Add inner glow
    ctx.globalAlpha = particle.opacity * 0.5;
    ctx.shadowBlur = 20;
    ctx.beginPath();
    ctx.arc(particle.x, particle.y, particle.size * 0.5, 0, Math.PI * 2);
    ctx.fill();
    
    ctx.restore();
  };

  const animate = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Resize canvas to match container
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;

    // Clear canvas with slight trail effect
    ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    if (isActive) {
      // Add new particles based on intensity
      const particleCount = Math.floor(intensity * 3) + 1;
      for (let i = 0; i < particleCount; i++) {
        if (particlesRef.current.length < 150) {
          particlesRef.current.push(createParticle(canvas));
        }
      }
    }

    // Update and draw particles
    particlesRef.current = particlesRef.current.filter(particle => {
      updateParticle(particle, canvas, intensity);
      drawParticle(ctx, particle);
      return particle.life < particle.maxLife;
    });

    animationFrameRef.current = requestAnimationFrame(animate);
  };

  useEffect(() => {
    animate();
    
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isActive, intensity]);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full pointer-events-none z-0"
      style={{ mixBlendMode: 'screen' }}
    />
  );
};

export default VoiceParticles;
