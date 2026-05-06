import React, { useState } from 'react';
import { StyleSheet, Text, View, ScrollView, TouchableOpacity, SafeAreaView, Alert } from 'react-native';
import RNPickerSelect from 'react-native-picker-select';

const COLORS = {
  darkGreen: '#003c33',
  lightGreen: '#edfce9',
  cream: '#eeece7',
  white: '#ffffff',
  text: '#212121',
  muted: '#93939f',
};

const BRANDS = [
  { label: '☀️ Luminous Solar', value: 'luminous' },
  { label: '⚡ Vikram Solar', value: 'vikram' },
  { label: '🔆 Jinko Solar', value: 'jinko' },
  { label: '💡 Microtek Solar', value: 'microtek' },
  { label: '🌟 Havells Solar', value: 'havells' },
  { label: '✨ Waaree Solar', value: 'waaree' },
  { label: '🔋 Canadian Solar', value: 'canadian' },
  { label: '⭐ Tata Solar', value: 'tata' },
];

const BRAND_INFO = {
  luminous: { name: 'Luminous Solar', warranty: '25 Years', efficiency: '18-20%' },
  vikram: { name: 'Vikram Solar', warranty: '25 Years', efficiency: '19-21%' },
  jinko: { name: 'Jinko Solar', warranty: '25 Years', efficiency: '20-22%' },
  microtek: { name: 'Microtek Solar', warranty: '25 Years', efficiency: '18-19%' },
  havells: { name: 'Havells Solar', warranty: '25 Years', efficiency: '18-20%' },
  waaree: { name: 'Waaree Solar', warranty: '25 Years', efficiency: '19-21%' },
  canadian: { name: 'Canadian Solar', warranty: '25 Years', efficiency: '20-21%' },
  tata: { name: 'Tata Solar', warranty: '25 Years', efficiency: '19-20%' },
};

export default function App() {
  const [selected, setSelected] = useState(null);
  const [showDetails, setShowDetails] = useState(false);

  const handleSelectBrand = (value) => {
    setSelected(value);
    setShowDetails(true);
  };

  const handleConfirm = () => {
    if (selected) {
      Alert.alert('✅ सफलता', `आप ${BRAND_INFO[selected].name} को चुना है!`);
    }
  };

  const handleChange = () => {
    setSelected(null);
    setShowDetails(false);
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerEmoji}>☀️🌾</Text>
          <Text style={styles.headerTitle}>VidyutSeva</Text>
          <Text style={styles.headerSubtitle}>खेत के लिए सही सौर पैनल चुनें</Text>
          <Text style={styles.headerSubtitleEng}>Choose Solar Panel for Your Farm</Text>
        </View>

        {/* Main Content */}
        <View style={styles.content}>
          {/* Info Section */}
          <View style={styles.infoSection}>
            <Text style={styles.infoTitle}>अपने सौर पैनल ब्रांड का चयन करें</Text>
            <Text style={styles.infoTitleEng}>Select your solar panel brand</Text>
          </View>

          {/* Dropdown */}
          <View style={styles.pickerWrapper}>
            <RNPickerSelect
              onValueChange={handleSelectBrand}
              items={BRANDS}
              placeholder={{ label: 'ब्रांड चुनें / Select Brand...', value: null }}
              value={selected}
              style={pickerStyles}
            />
          </View>

          {/* Selected Brand Details */}
          {showDetails && selected && BRAND_INFO[selected] && (
            <View style={styles.detailsCard}>
              <Text style={styles.detailsName}>{BRAND_INFO[selected].name}</Text>
              
              <View style={styles.detailsGrid}>
                <View style={styles.detailBox}>
                  <Text style={styles.detailLabel}>वारंटी</Text>
                  <Text style={styles.detailValue}>{BRAND_INFO[selected].warranty}</Text>
                </View>
                <View style={styles.detailBox}>
                  <Text style={styles.detailLabel}>दक्षता</Text>
                  <Text style={styles.detailValue}>{BRAND_INFO[selected].efficiency}</Text>
                </View>
              </View>

              <Text style={styles.detailsNote}>✓ भारत में उपलब्ध</Text>
            </View>
          )}

          {/* Features */}
          <View style={styles.featuresSection}>
            <Text style={styles.featuresTitle}>कुछ सुविधाएं / Features</Text>
            <View style={styles.featuresList}>
              <Text style={styles.featureItem}>🌞 उच्च दक्षता / High Efficiency</Text>
              <Text style={styles.featureItem}>⏱️ लंबी वारंटी / Long Warranty</Text>
              <Text style={styles.featureItem}>🏠 घर के लिए उपयुक्त / Home Suitable</Text>
              <Text style={styles.featureItem}>💰 सस्ती कीमत / Affordable Price</Text>
            </View>
          </View>

          {/* Buttons */}
          {selected && (
            <View style={styles.buttonGroup}>
              <TouchableOpacity style={styles.confirmButton} onPress={handleConfirm}>
                <Text style={styles.confirmButtonText}>✓ पुष्टि करें / Confirm</Text>
              </TouchableOpacity>

              <TouchableOpacity style={styles.changeButton} onPress={handleChange}>
                <Text style={styles.changeButtonText}>↻ फिर से चुनें / Change</Text>
              </TouchableOpacity>
            </View>
          )}

          {/* Footer */}
          <View style={styles.footer}>
            <Text style={styles.footerText}>🇮🇳 ग्रामीण भारत के लिए बनाया गया</Text>
            <Text style={styles.footerText}>Made for Rural India</Text>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.white,
  },
  scrollContent: {
    flexGrow: 1,
  },
  header: {
    backgroundColor: COLORS.darkGreen,
    paddingTop: 40,
    paddingBottom: 40,
    paddingHorizontal: 20,
    alignItems: 'center',
  },
  headerEmoji: {
    fontSize: 48,
    marginBottom: 10,
  },
  headerTitle: {
    fontSize: 36,
    fontWeight: 'bold',
    color: COLORS.white,
    marginBottom: 8,
  },
  headerSubtitle: {
    fontSize: 14,
    color: COLORS.lightGreen,
    marginBottom: 4,
  },
  headerSubtitleEng: {
    fontSize: 14,
    color: COLORS.cream,
  },
  content: {
    flex: 1,
    padding: 20,
  },
  infoSection: {
    backgroundColor: COLORS.lightGreen,
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
    borderLeftWidth: 4,
    borderLeftColor: COLORS.darkGreen,
  },
  infoTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.darkGreen,
  },
  infoTitleEng: {
    fontSize: 12,
    color: COLORS.muted,
    marginTop: 4,
  },
  pickerWrapper: {
    borderWidth: 2,
    borderColor: COLORS.darkGreen,
    borderRadius: 10,
    marginBottom: 20,
    backgroundColor: COLORS.white,
  },
  detailsCard: {
    backgroundColor: COLORS.lightGreen,
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
    borderLeftWidth: 5,
    borderLeftColor: COLORS.darkGreen,
  },
  detailsName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: COLORS.darkGreen,
    marginBottom: 12,
  },
  detailsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 12,
  },
  detailBox: {
    flex: 1,
    backgroundColor: COLORS.white,
    borderRadius: 8,
    padding: 10,
    marginHorizontal: 5,
    alignItems: 'center',
  },
  detailLabel: {
    fontSize: 11,
    color: COLORS.muted,
    marginBottom: 4,
  },
  detailValue: {
    fontSize: 14,
    fontWeight: 'bold',
    color: COLORS.darkGreen,
  },
  detailsNote: {
    textAlign: 'center',
    fontSize: 12,
    color: COLORS.darkGreen,
    fontWeight: '500',
  },
  featuresSection: {
    marginBottom: 20,
  },
  featuresTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: 10,
  },
  featuresList: {
    backgroundColor: COLORS.cream,
    borderRadius: 10,
    padding: 12,
  },
  featureItem: {
    fontSize: 13,
    color: COLORS.text,
    paddingVertical: 6,
  },
  buttonGroup: {
    marginBottom: 20,
  },
  confirmButton: {
    backgroundColor: COLORS.darkGreen,
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
    marginBottom: 10,
  },
  confirmButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: COLORS.white,
  },
  changeButton: {
    backgroundColor: COLORS.cream,
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: COLORS.darkGreen,
  },
  changeButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: COLORS.darkGreen,
  },
  footer: {
    alignItems: 'center',
    paddingVertical: 20,
  },
  footerText: {
    fontSize: 12,
    color: COLORS.muted,
    marginVertical: 2,
  },
});

const pickerStyles = StyleSheet.create({
  inputIOS: {
    fontSize: 16,
    paddingVertical: 12,
    paddingHorizontal: 10,
    borderRadius: 8,
    color: COLORS.darkGreen,
    fontWeight: '600',
  },
  inputAndroid: {
    fontSize: 16,
    paddingHorizontal: 10,
    paddingVertical: 8,
    borderRadius: 8,
    color: COLORS.darkGreen,
    fontWeight: '600',
  },
});
