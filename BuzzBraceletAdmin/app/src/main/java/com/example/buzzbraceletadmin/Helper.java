package com.example.buzzbraceletadmin;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.nio.charset.StandardCharsets;

import javax.crypto.Cipher;
import javax.crypto.spec.SecretKeySpec;

public class Helper {
    public static String getSHA256Hash(String message) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            return bytesToHex(md.digest(message.getBytes(StandardCharsets.UTF_8)));
        } catch (NoSuchAlgorithmException e) {
            e.printStackTrace();
        }
        return null;
    }

    // public static String bytesToHex(byte[] bytes) {
    //     StringBuilder sb = new StringBuilder();
    //     for (byte b : bytes) {
    //         sb.append(String.format("%02x", b));
    //     }
    //     return sb.toString();
    // }

    private static final char[] HEX_ARRAY = "0123456789abcdef".toCharArray();

    public static String bytesToHex(byte[] bytes) {
        char[] hexChars = new char[bytes.length * 2];
        for (int j = 0; j < bytes.length; j++) {
            int v = bytes[j] & 0xFF;
            hexChars[j * 2] = HEX_ARRAY[v >>> 4];
            hexChars[j * 2 + 1] = HEX_ARRAY[v & 0x0F];
        }
        return new String(hexChars);
    }

    public static byte[] hexToBytes(String s) {
        int len = s.length();
        byte[] str = new byte[len / 2];
        for (int i = 0; i < len; i += 2) {
            str[i / 2] = (byte) ((Character.digit(s.charAt(i), 16) << 4) + Character.digit(s.charAt(i+1), 16));
        }
        return str;
    }

    public static byte[] encryptAES(byte[] plainText, String password){
        try{
            SecretKeySpec secretKey = new SecretKeySpec(MessageDigest.getInstance("SHA-256").digest(password.getBytes()), "AES");
            Cipher cipher = Cipher.getInstance("AES");
            cipher.init(Cipher.ENCRYPT_MODE, secretKey);
            return cipher.doFinal(plainText);
        } catch (Exception e){
            e.printStackTrace();
        }
        return null;
    }

    public static byte[] decryptAES(byte[] cipherText, String password){
        try {
            SecretKeySpec secretKey = new SecretKeySpec(MessageDigest.getInstance("SHA-256").digest(password.getBytes()), "AES");
            Cipher cipher = Cipher.getInstance("AES");
            cipher.init(Cipher.DECRYPT_MODE, secretKey);
            return cipher.doFinal(cipherText);
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }
}

