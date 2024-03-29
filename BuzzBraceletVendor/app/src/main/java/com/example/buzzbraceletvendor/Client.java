package com.example.buzzbraceletvendor;

import android.util.Base64;

import java.io.File;
import java.security.InvalidKeyException;
import java.security.KeyFactory;
import java.security.NoSuchAlgorithmException;
import java.security.PrivateKey;
import java.security.PublicKey;
import java.security.Signature;
import java.security.SignatureException;
import java.security.spec.PKCS8EncodedKeySpec;
import java.security.spec.X509EncodedKeySpec;
import java.util.Scanner;

public class Client {
    public String name;
    private PrivateKey private_key;
    public PublicKey public_key;

    public Client(File f) {
        try {
            Scanner file = new Scanner(f);
            file.useDelimiter("\n");
            this.name = file.next();
            String private_key = file.next();
            String public_key = file.next();
            file.close();

            private_key = private_key.replace("-----BEGIN PRIVATE KEY-----", "").replace("-----END PRIVATE KEY-----",
                    "");
            private_key = private_key.replace("\n", "").replace("\r", "");
            byte[] privkey = Base64.decode(private_key, Base64.DEFAULT);           //FIX FLAGS!!

            public_key = public_key.replace("-----BEGIN PUBLIC KEY-----", "").replace("-----END PUBLIC KEY-----", "");
            public_key = public_key.replace("\n", "").replace("\r", "");
            byte[] pubkey = Base64.decode(public_key, Base64.DEFAULT);         //FIX!!

            KeyFactory factory = KeyFactory.getInstance("EC");
            this.private_key = factory.generatePrivate(new PKCS8EncodedKeySpec(privkey));
            this.public_key = factory.generatePublic(new X509EncodedKeySpec(pubkey));
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public void sign(Transaction t) {
        try {
            byte[] msg = Helper.hexToBytes(t.getHash());
            Signature signer = Signature.getInstance("SHA256withECDSA");
            signer.initSign(this.private_key);
            signer.update(msg);
            byte[] signature = signer.sign();
            t.signature = Helper.bytesToHex(signature);
        } catch (InvalidKeyException | NoSuchAlgorithmException | SignatureException e) {
            e.printStackTrace();
        }
    }

    public String getIdentity(){
        return Helper.bytesToHex(this.public_key.getEncoded()).substring(48);
    }
}