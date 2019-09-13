package com.example.peng.nfcreadwrite;

import java.io.File;
import java.io.FileNotFoundException;
import java.util.Scanner;
import java.util.ArrayList;

public class Test {
    public static void main(String[] args) {
        Client c = new Client();
        String s = "4e9c1e4cc987bdd7b63735d3b32b733be639eb98f0ded1b1022fdf1070a090f06489458acf8c947d01b71aadd0f5e7ec1585a2eda932d873d2006c2856b8e43904c5ef69f1e6ae374618e4a8b8bf46ab659cc7bccf7f95ad36b9522601c02b68";

        Transaction t = new Transaction(s, c.getIdentity(), 20);
        c.sign(t);
        // System.out.println(t.toJson());
        // System.out.println(t.getHash());

        Blockchain chain = new Blockchain();
        ArrayList<Transaction> l = new ArrayList<Transaction>();
        l.add(t);
        try {
            chain.genesis(l);
            chain.export();
        } catch (Exception e) {
            e.printStackTrace();
        }

        System.out.println(chain.getHash());

        Scanner file;
        String j = "";
        try {
            file = new Scanner(new File("blockchain.json"));
            file.useDelimiter("\\Z");
            j = file.next();
            file.close();
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        }
        chain.rebuild(j);
        System.out.println(chain.getHash());
    }
}