import { useState } from 'react';
import './Slider.css';

export default function CardSlider({ cards = [], visibleCount = 2 }) {
  const [currentIndex, setCurrentIndex] = useState(0);

  const nextCard = () => {
    setCurrentIndex((prev) => (prev + visibleCount) % cards.length);
  };

  const prevCard = () => {
    setCurrentIndex((prev) =>
      (prev - visibleCount + cards.length) % cards.length
    );
  };

  const getVisibleCards = () => {
    return Array.from({ length: visibleCount }, (_, i) => {
      const index = (currentIndex + i) % cards.length;
      return cards[index];
    });
  };

  return (
    <div className="slider-container">
      <button onClick={prevCard} className="nav-button">←</button>

      <div className="card-wrapper">
        {getVisibleCards().map((card) => (
          <div className="card" key={card.id}>
            <h2>{card.title}</h2>
            <p>{card.description}</p>
          </div>
        ))}
      </div>

      <button onClick={nextCard} className="nav-button">→</button>
    </div>
  );
}
