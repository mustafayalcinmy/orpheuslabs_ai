
import logging
import subprocess
import pretty_midi
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import os
from pydub import AudioSegment
import random
import math


logger = logging.getLogger("MusicGen")

def midi_to_sequence(midi_path):
    """
    MIDI dosyasını yükler ve basitçe notaların pitch değerlerini içeren bir liste oluşturur.
    (Not: Daha sofistike zaman/dinamik temsilleri için ek işleme gerekebilir.)
    """
    try:
        midi_data = pretty_midi.PrettyMIDI(midi_path)
    except Exception as e:
        logger.error(f"MIDI yüklenirken hata: {e}")
        return None

    sequence = []
    for instrument in midi_data.instruments:
        if instrument.is_drum:
            continue
        for note in instrument.notes:
            sequence.append(note.pitch)
    return sequence


def sequence_to_midi(sequence, file_path='generated_music.mid', bpm=120, note_duration=0.5, instrument_program=0):
    """
    Pitch dizisini MIDI dosyasına dönüştürür.
    
    Parametreler:
    sequence: MIDI pitch değerlerinin listesi (0-127)
    file_path: Çıktı dosyasının yolu
    bpm: Dakikadaki vuruş sayısı (tempo)
    note_duration: Her notanın saniye cinsinden süresi
    instrument_program: MIDI program numarası (enstrüman türü)
    """
    midi = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=instrument_program)

    tempo = bpm
    seconds_per_beat = 60.0 / tempo
    current_time = 0.0

    for pitch in sequence:
        note = pretty_midi.Note(
            velocity=100, 
            pitch=pitch,
            start=current_time,
            end=current_time + note_duration
        )
        instrument.notes.append(note)
        current_time += note_duration * 0.5 
    midi.instruments.append(instrument)
    midi.write(file_path)
    return file_path

def enhance_midi_quality(midi_path, output_path, bpm=120, instrument_program=0):
    """
    MIDI dosyasının kalitesini artırmak için daha gelişmiş parametreler ekler
    """
    try:
        midi = pretty_midi.PrettyMIDI(midi_path)
    except Exception as e:
        logger.error(f"MIDI yüklenirken hata: {e}")
        return None

    # Yeni MIDI objesi oluştur
    enhanced_midi = pretty_midi.PrettyMIDI()
    new_instrument = pretty_midi.Instrument(program=instrument_program)

    # Nota parametrelerini iyileştirme
    for instr in midi.instruments:  # Dışarıdaki instrument'ı 'instr' olarak değiştirdik
        for note in instr.notes:
            # Rastgele velocity ekle (60-127 arası)
            velocity = random.randint(60, 127)
            
            # Nota süresine rastgele varyasyon ekle
            duration = note.end - note.start
            duration_variation = duration * random.uniform(0.9, 1.1)
            
            enhanced_note = pretty_midi.Note(
                velocity=velocity,
                pitch=note.pitch,
                start=note.start,
                end=note.start + duration_variation
            )
            new_instrument.notes.append(enhanced_note)

    enhanced_midi.instruments.append(new_instrument)
    
    enhanced_midi.write(output_path)
    return output_path


def midi_to_wav(midi_path, wav_path, soundfont_path):
    """
    MIDI'yi WAV'a dönüştürür (FluidSynth gerektirir)
    """
    try:
        subprocess.run([
            'fluidsynth', '-ni', soundfont_path, 
            midi_path, '-F', wav_path, '-r', '44100', '-q'
        ], check=True, timeout=10)
        return wav_path
    except Exception as e:
        logger.error(f"WAV dönüşüm hatası: {e}")
        return None
    except FileNotFoundError:
        logger.error("FluidSynth kurulu değil! Lütfen kurulum yapın.")
        return None


def convert_to_mp3(wav_path, mp3_path, bitrate='192k'):
    """
    WAV dosyasını MP3'e dönüştürür
    """
    try:
        audio = AudioSegment.from_wav(wav_path)
        audio.export(mp3_path, format="mp3", bitrate=bitrate)
        return mp3_path
    except Exception as e:
        logger.error(f"MP3 dönüşüm hatası: {e}")
        return None




def visualize_midi_piano_roll(midi_path, output_png_path=None, instrument_index=0):
    """
    Verilen MIDI dosyasını piyano rulosu olarak görselleştirir ve kaydeder.

    Args:
        midi_path (str): Görselleştirilecek MIDI dosyasının yolu.
        output_png_path (str, optional): Görselleştirmenin kaydedileceği PNG dosyasının yolu.
                                         None ise, MIDI dosyasıyla aynı isimde .png uzantılı kaydeder.
        instrument_index (int): Görselleştirilecek enstrümanın indeksi (0'dan başlar).
    """
    try:
        # MIDI dosyasını yükle
        midi_data = pretty_midi.PrettyMIDI(midi_path)
        logger.info(f"MIDI Görselleştirme için Yüklendi: {os.path.basename(midi_path)}")

        if not midi_data.instruments:
            logger.warning("Görselleştirme için MIDI dosyasında enstrüman bulunamadı.")
            return False

        if instrument_index >= len(midi_data.instruments):
            logger.warning(f"Geçersiz enstrüman indeksi ({instrument_index}). İlk enstrüman (0) kullanılacak.")
            instrument_index = 0
            if not midi_data.instruments: # Tekrar kontrol (ilk enstrüman da olmayabilir)
                 logger.warning("Görselleştirme için MIDI dosyasında enstrüman bulunamadı.")
                 return False

        instrument = midi_data.instruments[instrument_index]
        logger.info(f"Görselleştirilen Enstrüman ({instrument_index}): {instrument.name} (Program: {instrument.program})")

        if instrument.is_drum:
            logger.info("Uyarı: Seçilen enstrüman bir davul kanalı. Piyano rulosu görselleştirmesi yapılıyor.")

        notes = instrument.notes
        if not notes:
            logger.info(f"'{instrument.name}' enstrümanında görselleştirilecek nota bulunamadı.")
            return False

        # Çıktı dosya yolunu belirle
        if output_png_path is None:
            output_png_path = os.path.splitext(midi_path)[0] + ".png"

        # --- Piyano Rulosu Çizimi ---
        fig, ax = plt.subplots(figsize=(20, 6))
        ax.set_xlabel("Zaman (saniye)")
        ax.set_ylabel("Nota Perdesi (MIDI Numarası)")
        ax.set_title(f"Piyano Rulosu - {os.path.basename(midi_path)} - Enstrüman: {instrument.name}")

        min_pitch = min(note.pitch for note in notes)
        max_pitch = max(note.pitch for note in notes)
        ax.set_ylim(min_pitch - 2, max_pitch + 2)
        ax.set_xlim(0, midi_data.get_end_time())

        # Notaları dikdörtgen olarak ekle
        for note in notes:
            start = note.start
            end = note.end
            duration = end - start
            pitch = note.pitch
            # Velocity'yi 0-1 arasına normalize et, 0 velocity için minimum alpha/renk ayarla
            velocity = note.velocity / 127.0 if note.velocity > 0 else 0.0
            color_intensity = max(0.1, velocity) # Çok düşük velocity'ler için minimum parlaklık

            rect = patches.Rectangle(
                (start, pitch - 0.5),
                duration,
                1,
                linewidth=0.5, # Daha ince kenarlık
                edgecolor='grey', # Daha soluk kenarlık
                facecolor=plt.cm.viridis(color_intensity), # Renk velocity'ye göre
                alpha=max(0.3, velocity) # Şeffaflık velocity'ye göre (minimum alpha)
            )
            ax.add_patch(rect)

        ax.set_yticks(np.arange(min_pitch, max_pitch + 1, 5))
        ax.grid(True, axis='y', linestyle=':', color='gray', alpha=0.5)
        plt.tight_layout()

        # Grafiği kaydet
        plt.savefig(output_png_path)
        logger.info(f"MIDI Görselleştirmesi kaydedildi: {output_png_path}")
        plt.close(fig) # Figürü kapatarak hafızayı boşalt
        return True

    except FileNotFoundError:
        logger.error(f"Hata: MIDI dosyası bulunamadı: {midi_path}")
        return False
    except ImportError:
        logger.error("Hata: Matplotlib veya Numpy kütüphaneleri kurulu değil. Lütfen 'pip install matplotlib numpy' ile kurun.")
        return False
    except Exception as e:
        logger.error(f"MIDI görselleştirilirken bir hata oluştu ({midi_path}): {e}", exc_info=True)
        # Hata durumunda figür açık kalmışsa kapat
        if 'fig' in locals() and plt.fignum_exists(fig.number):
             plt.close(fig)
        return False
    

def midi_to_pianoroll_tensor(midi_path, fs=4, pitch_range=(24, 108), include_velocity=False):
    """
    MIDI dosyasını piyano rulosu tensörüne dönüştürür.

    Args:
        midi_path (str): MIDI dosyasının yolu.
        fs (int): Saniyedeki zaman adımı sayısı (çözünürlük).
        pitch_range (tuple): Kullanılacak MIDI nota aralığı (min_pitch, max_pitch).
        include_velocity (bool): Tensörde velocity bilgisini (0-1) sakla (True)
                                 veya sadece varlığı (0/1) sakla (False).

    Returns:
        np.ndarray: Piyano rulosu tensörü (Zaman Adımları, Nota Sayısı) veya None (hata durumunda).
    """
    try:
        midi_data = pretty_midi.PrettyMIDI(midi_path)
        end_time = midi_data.get_end_time()
        num_time_steps = math.ceil(end_time * fs)
        num_pitches = pitch_range[1] - pitch_range[0]

        if num_pitches <= 0:
             logger.error("Geçersiz pitch_range.")
             return None

        # Başlangıçta sıfırlarla dolu bir piyano rulosu matrisi oluştur
        piano_roll = np.zeros((num_time_steps, num_pitches))

        for instrument in midi_data.instruments:
            if instrument.is_drum:
                continue # Davulları atla
            for note in instrument.notes:
                # Nota pitch'i belirlenen aralıkta mı kontrol et
                if pitch_range[0] <= note.pitch < pitch_range[1]:
                    # Nota başlangıç ve bitiş zamanlarını zaman adımlarına dönüştür
                    start_step = int(round(note.start * fs))
                    end_step = int(round(note.end * fs))

                    # Nota pitch'ini matris indeksine dönüştür
                    pitch_index = note.pitch - pitch_range[0]

                    # Zaman adımlarına notayı işle
                    if start_step < num_time_steps:
                        # Velocity veya sabit 1 değeri ata
                        value = note.velocity / 127.0 if include_velocity else 1.0
                        # Aynı anda başlayan notalar için max velocity'yi alabiliriz (opsiyonel)
                        piano_roll[start_step:min(end_step, num_time_steps), pitch_index] = np.maximum(
                            piano_roll[start_step:min(end_step, num_time_steps), pitch_index],
                            value
                        )

        return piano_roll.astype(np.float32) # Float32'ye çevir

    except Exception as e:
        logger.error(f"MIDI'den piyano rulosuna dönüştürme hatası ({midi_path}): {e}", exc_info=True)
        return None

# --- Piyano Rulosu -> MIDI dönüşümü de gerekecek ---
def pianoroll_tensor_to_midi(piano_roll, file_path='output_from_gan.mid', fs=4, pitch_range=(24, 108), velocity_threshold=0.1, note_duration_steps=1, instrument_program=0, bpm=120):
    """
    Piyano rulosu tensörünü MIDI dosyasına dönüştürür.

    Args:
        piano_roll (np.ndarray): Piyano rulosu (Zaman Adımları, Nota Sayısı).
        file_path (str): Kaydedilecek MIDI dosyasının yolu.
        fs (int): Saniyedeki zaman adımı sayısı (tensörle aynı olmalı).
        pitch_range (tuple): Kullanılan MIDI nota aralığı (tensörle aynı olmalı).
        velocity_threshold (float): Bir notanın aktif kabul edilmesi için minimum değer (0-1).
        note_duration_steps (int): Minimum nota süresi (zaman adımı cinsinden).
        instrument_program (int): Kullanılacak enstrüman program numarası.
        bpm (int): Tempo.
    """
    try:
        midi = pretty_midi.PrettyMIDI(initial_tempo=bpm)
        instrument = pretty_midi.Instrument(program=instrument_program)
        num_time_steps, num_pitches = piano_roll.shape
        min_pitch = pitch_range[0]
        seconds_per_step = 1.0 / fs

        current_notes = {} # Aktif notaları takip etmek için: pitch -> (start_step, velocity)

        for time_step in range(num_time_steps):
            current_time = time_step * seconds_per_step
            for pitch_index in range(num_pitches):
                pitch = min_pitch + pitch_index
                velocity_value = piano_roll[time_step, pitch_index]
                is_active = velocity_value >= velocity_threshold

                if pitch in current_notes: # Nota zaten aktif mi?
                    if not is_active: # Nota bitti mi?
                        start_step, start_velocity = current_notes.pop(pitch)
                        duration_steps = time_step - start_step
                        if duration_steps >= note_duration_steps:
                            note = pretty_midi.Note(
                                velocity=int(start_velocity * 127),
                                pitch=pitch,
                                start=start_step * seconds_per_step,
                                end=time_step * seconds_per_step
                            )
                            instrument.notes.append(note)
                    # else: Nota devam ediyor, bir şey yapma
                else: # Nota aktif değil miydi?
                     if is_active: # Yeni nota başladı mı?
                         current_notes[pitch] = (time_step, velocity_value)

        # Döngü bittikten sonra hala aktif olan notaları bitir
        final_time = num_time_steps * seconds_per_step
        for pitch, (start_step, start_velocity) in current_notes.items():
             duration_steps = num_time_steps - start_step
             if duration_steps >= note_duration_steps:
                 note = pretty_midi.Note(
                     velocity=int(start_velocity * 127),
                     pitch=pitch,
                     start=start_step * seconds_per_step,
                     end=final_time
                 )
                 instrument.notes.append(note)


        midi.instruments.append(instrument)
        midi.write(file_path)
        logger.info(f"Piyano rulosundan MIDI oluşturuldu: {file_path}")
        return file_path

    except Exception as e:
         logger.error(f"Piyano rulosundan MIDI'ye dönüştürme hatası: {e}", exc_info=True)
         return None