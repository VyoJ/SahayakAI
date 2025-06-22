
import { useEffect, useRef } from 'react';

interface WaveformVisualizerProps {
  audioLevel: number;
}

const WaveformVisualizer = ({ audioLevel }: WaveformVisualizerProps) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const animationFrameRef = useRef<number>();

  useEffect(() => {
    const animate = () => {
      if (!svgRef.current) return;

      const circles = svgRef.current.querySelectorAll('circle');
      circles.forEach((circle, index) => {
        const baseRadius = 85 + (index * 15);
        const variation = Math.sin(Date.now() * 0.005 + index * 0.5) * audioLevel * 20;
        const radius = baseRadius + variation;
        
        circle.setAttribute('r', radius.toString());
        circle.setAttribute('opacity', (audioLevel * 0.6 + 0.2 - index * 0.1).toString());
      });

      animationFrameRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [audioLevel]);

  return (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
      <svg
        ref={svgRef}
        width="400"
        height="400"
        className="absolute"
        style={{ transform: 'translate(-50%, -50%)', left: '50%', top: '50%' }}
      >
        {/* Outer rings */}
        {[0, 1, 2, 3].map((index) => (
          <circle
            key={index}
            cx="200"
            cy="200"
            r={85 + index * 15}
            fill="none"
            stroke={`rgba(147, 51, 234, ${0.6 - index * 0.1})`}
            strokeWidth="2"
            className="animate-pulse"
            style={{
              animationDelay: `${index * 0.2}s`,
              filter: 'blur(1px)'
            }}
          />
        ))}
        
        {/* Inner pulsing circle */}
        <circle
          cx="200"
          cy="200"
          r="70"
          fill="rgba(147, 51, 234, 0.1)"
          stroke="rgba(147, 51, 234, 0.3)"
          strokeWidth="1"
          className="animate-pulse"
        />
      </svg>
      
      {/* Floating orbs */}
      <div className="absolute inset-0">
        {[...Array(8)].map((_, index) => (
          <div
            key={index}
            className="absolute w-2 h-2 bg-purple-400 rounded-full animate-ping"
            style={{
              left: `${50 + Math.cos((index * Math.PI * 2) / 8) * 30}%`,
              top: `${50 + Math.sin((index * Math.PI * 2) / 8) * 30}%`,
              animationDelay: `${index * 0.2}s`,
              animationDuration: '2s'
            }}
          />
        ))}
      </div>
    </div>
  );
};

export default WaveformVisualizer;
