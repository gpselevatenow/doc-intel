import React, { useState, useEffect } from 'react';

const TypewriterValue = ({ value, delay = 0, speed = 80, resetKey = '' }) => {
  const isEmpty = !value || value === '—' || value === 'Unknown' || value === 'N/A' || value === 'n/a';
  const [displayed, setDisplayed] = useState('');
  const [done, setDone] = useState(false);

  useEffect(() => {
    console.log('TypewriterValue mounting:', value, 'delay:', delay);
    if (isEmpty) {
      setDisplayed('—');
      setDone(true);
      return;
    }
    setDisplayed('');
    setDone(false);

    let intervalId;
    const timeoutId = setTimeout(() => {
      let i = 0;
      intervalId = setInterval(() => {
        i++;
        setDisplayed(value.slice(0, i));
        if (i >= value.length) {
          clearInterval(intervalId);
          setDone(true);
        }
      }, speed);
    }, delay);

    return () => {
      clearTimeout(timeoutId);
      if (intervalId) clearInterval(intervalId);
    };
  }, [value, delay, resetKey]);

  if (isEmpty) return <span>—</span>;

  return (
    <span>
      {displayed}
      {!done && <span className="tw-cursor">|</span>}
    </span>
  );
};

export default TypewriterValue;
