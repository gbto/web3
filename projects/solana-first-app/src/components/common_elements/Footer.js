import React from 'react';
import './Footer.css';
import { Button } from './Button';
import { Link } from 'react-router-dom';

function Footer() {
  return (
    <div className="footer-container">
      <section className="footer-subscription">
        <p className="footer-subscription-heading">Wanna get in touch ?</p>
        <p className="footer-subscription-text">Send me your email!</p>
        <div className="input-areas">
          <form>
            <input
              className="footer-input"
              name="email"
              type="email"
              placeholder="Your Email"
            />
            <Button buttonStyle="btn--outline">Reach out</Button>
          </form>
        </div>
      </section>

      <section className="social-media">
        <div className="social-media-wrap">
          <div className="footer-logo">
            <Link to="/" className="social-logo">
              GBTO
              <i className="fab fa-typo3" />
            </Link>
          </div>
          <small className="website-rights">gibboneto © 2021</small>
          <div className="social-icons">
            <Link
              className="social-icon-link github"
              to="https://github.com/gbto"
              target="_blank"
              aria-label="Github"
            >
              <i className="fab fa-github"> fa-github </i>
            </Link>
            <Link
              className="social-icon-link linkedin"
              to="https://fr.linkedin.com/in/quentin-gaborit"
              target="_blank"
              aria-label="LinkedIn"
            >
              <i className="fab fa-linkedin-in"> fa-linkedin </i>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}

export default Footer;
