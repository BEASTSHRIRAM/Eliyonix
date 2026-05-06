import React, { useState } from 'react';
import {
  IonPage,
  IonHeader,
  IonToolbar,
  IonTitle,
  IonContent,
  IonCard,
  IonCardContent,
  IonCardHeader,
  IonCardTitle,
  IonButton,
  IonSelect,
  IonSelectOption,
  IonAlert,
  IonLoading,
  IonText,
  IonGrid,
  IonRow,
  IonCol,
  useIonAlert,
} from '@ionic/react';
import { submitBrandSelection } from '../services/api';
import './SolarBrandSelector.css';

const SOLAR_BRANDS = [
  {
    id: 'luminous',
    name: '🌞 Luminous',
    warranty: '25 years',
    efficiency: '22%',
    description: 'Premium Indian solar solutions',
    hindiName: 'लुमिनस',
  },
  {
    id: 'vikram',
    name: '⚡ Vikram',
    warranty: '25 years',
    efficiency: '20%',
    description: 'Reliable solar inverters',
    hindiName: 'विक्रम',
  },
  {
    id: 'jinko',
    name: '🔆 Jinko',
    warranty: '25 years',
    efficiency: '21%',
    description: 'World-leading solar panels',
    hindiName: 'जिंको',
  },
  {
    id: 'microtek',
    name: '💚 Microtek',
    warranty: '25 years',
    efficiency: '19%',
    description: 'Indian solar innovators',
    hindiName: 'माइक्रोटेक',
  },
  {
    id: 'havells',
    name: '⭐ Havells',
    warranty: '25 years',
    efficiency: '20%',
    description: 'Trusted energy solutions',
    hindiName: 'हवेल्स',
  },
  {
    id: 'waaree',
    name: '🌱 Waaree',
    warranty: '25 years',
    efficiency: '20%',
    description: 'Green energy leader',
    hindiName: 'वारी',
  },
  {
    id: 'canadian',
    name: '🇨🇦 Canadian',
    warranty: '25 years',
    efficiency: '22%',
    description: 'Global solar technology',
    hindiName: 'कनाडियन',
  },
  {
    id: 'tata',
    name: '🏢 Tata',
    warranty: '25 years',
    efficiency: '21%',
    description: 'Indian conglomerate brand',
    hindiName: 'टाटा',
  },
];

const SolarBrandSelector: React.FC = () => {
  const [selectedBrand, setSelectedBrand] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [showAlert, setShowAlert] = useState(false);
  const [alertMessage, setAlertMessage] = useState('');
  const [presentAlert] = useIonAlert();

  const selectedBrandData = SOLAR_BRANDS.find((b) => b.id === selectedBrand);

  const handleSubmit = async () => {
    if (!selectedBrand) {
      presentAlert({
        header: 'Select a Brand',
        message: 'कृपया एक ब्रांड चुनें (Please select a brand)',
        buttons: ['OK'],
      });
      return;
    }

    setLoading(true);
    try {
      const response = await submitBrandSelection(selectedBrand, 'farmer_001');
      setAlertMessage(`✅ ${response.brand} selected successfully!\n\n${response.message}`);
      setShowAlert(true);
      setSelectedBrand('');
    } catch (error) {
      setAlertMessage(`❌ Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setShowAlert(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <IonPage>
      <IonHeader>
        <IonToolbar color="primary">
          <IonTitle>🌾 VidyutSeva Solar</IonTitle>
        </IonToolbar>
      </IonHeader>
      <IonContent fullscreen>
        <div className="solar-container">
          <IonCard className="header-card">
            <IonCardContent>
              <h1>Select Your Solar Panel Brand</h1>
              <p className="subtitle">चुनें अपना सौर पैनल ब्रांड</p>
              <p className="description">
                Choose from India's top solar manufacturers. All brands offer 25-year warranties.
              </p>
            </IonCardContent>
          </IonCard>

          <IonCard className="selector-card">
            <IonCardHeader>
              <IonCardTitle>Available Brands</IonCardTitle>
            </IonCardHeader>
            <IonCardContent>
              <IonSelect
                placeholder="Select a solar brand..."
                value={selectedBrand}
                onIonChange={(e) => setSelectedBrand(e.detail.value)}
                className="brand-select"
              >
                {SOLAR_BRANDS.map((brand) => (
                  <IonSelectOption key={brand.id} value={brand.id}>
                    {brand.name}
                  </IonSelectOption>
                ))}
              </IonSelect>
            </IonCardContent>
          </IonCard>

          {selectedBrandData && (
            <IonCard className="brand-details-card">
              <IonCardHeader>
                <IonCardTitle>{selectedBrandData.name}</IonCardTitle>
              </IonCardHeader>
              <IonCardContent>
                <IonGrid>
                  <IonRow>
                    <IonCol size="6">
                      <div className="detail-item">
                        <h3>Warranty</h3>
                        <p className="detail-value">{selectedBrandData.warranty}</p>
                      </div>
                    </IonCol>
                    <IonCol size="6">
                      <div className="detail-item">
                        <h3>Efficiency</h3>
                        <p className="detail-value">{selectedBrandData.efficiency}</p>
                      </div>
                    </IonCol>
                  </IonRow>
                  <IonRow>
                    <IonCol>
                      <div className="detail-item">
                        <h3>Description</h3>
                        <p>{selectedBrandData.description}</p>
                      </div>
                    </IonCol>
                  </IonRow>
                  <IonRow>
                    <IonCol>
                      <div className="detail-item">
                        <h3>Hindi Name</h3>
                        <p className="hindi-text">{selectedBrandData.hindiName}</p>
                      </div>
                    </IonCol>
                  </IonRow>
                </IonGrid>
              </IonCardContent>
            </IonCard>
          )}

          <div className="button-group">
            <IonButton
              expand="block"
              color="primary"
              onClick={handleSubmit}
              disabled={!selectedBrand || loading}
              className="confirm-button"
            >
              {loading ? 'Confirming...' : '✓ Confirm Selection'}
            </IonButton>
            {selectedBrand && (
              <IonButton
                expand="block"
                fill="outline"
                color="primary"
                onClick={() => setSelectedBrand('')}
                className="reset-button"
              >
                Change Brand
              </IonButton>
            )}
          </div>
        </div>

        <IonLoading isOpen={loading} message="Processing..." />
        <IonAlert
          isOpen={showAlert}
          onDidDismiss={() => setShowAlert(false)}
          header="Selection Result"
          message={alertMessage}
          buttons={['OK']}
        />
      </IonContent>
    </IonPage>
  );
};

export default SolarBrandSelector;
